from pandas import DataFrame
from typing import Union, List, Tuple
from tqdm import tqdm
import traceback
import os

from .utils import write_report
from .dset_stage import DatasetStage
from .row_stage import RowStage
from .stage import Stage
from .utils import cleanup_storage
from .mlcube_constants import DONE_STAGE_STATUS


class Pipeline:
    def __init__(
        self,
        init_stage: DatasetStage,
        stages: List[Union[DatasetStage, RowStage]],
        staging_folders: List[str],
        trash_folders: List[str],
        invalid_subjects_file: str,
    ):
        self.init_stage = init_stage
        self.stages = stages
        self.staging_folders = staging_folders
        self.trash_folders = trash_folders
        self.invalid_subjects_file = invalid_subjects_file

    def __invalid_subjects(self) -> List[str]:
        """Retrieve invalid subjects

        Returns:
            List[str]: list of invalid subjects
        """
        if not os.path.exists(self.invalid_subjects_file):
            open(self.invalid_subjects_file, "a").close()

        with open(self.invalid_subjects_file, "r") as f:
            invalid_subjects = set([line.strip() for line in f])

        return invalid_subjects

    def __is_subject_done(self, subject: Union[str, int], report: DataFrame) -> bool:
        """Determines if a subject is considered done

        Args:
            subject (Union[str, int]): subject index
            report (DataFrame): DataFrame containing the state of the processing

        Returns:
            bool: wether the subject is done or not
        """
        subject_status = report.loc[subject, "status"]

        return subject_status == DONE_STAGE_STATUS

    def __is_done(self, report: DataFrame) -> bool:
        """Determines if the preparation is complete

        Args:
            report (DataFrame): DataFrame containing the state of the processing

        Returns:
            bool: Wether the preparation is complete
        """
        return all(report["status"] == DONE_STAGE_STATUS)

    def __get_report_stage_to_run(
        self, subject: Union[str, int], report: DataFrame
    ) -> Union[DatasetStage, RowStage]:
        """Retrieves the stage a subject is in indicated by the report

        Args:
            subject (Union[str, int]): Subject index
            report (DataFrame): Dataframe containing the state of the processing

        Returns:
            Union[DatasetStage, RowStage]: Stage the current subject is in
        """
        report_status_code = int(report.loc[subject, "status"])
        if report_status_code < 0:
            # Error code, rerun the stage specified in the report
            report_status_code = abs(report_status_code)
        else:
            # Success code, reported stage works so move to the next one
            report_status_code += 1
        for stage in self.stages:
            if stage.status_code == report_status_code:
                return stage

        return None

    def determine_next_stage(
        self, subject: Union[str, int], report
    ) -> Tuple[List[Union[DatasetStage, RowStage]], bool]:
        """Determines what stage to run
        First priority goes to a stage if it is the only one that could run. (only one stage can run)
        Second priority goes to what the report says should run next. (The report knows what stage can run)
        Third priority goes to the first of all possible stages that could run. (Earliest of all possible stages)

        Args:
            subject (Union[str, int]): Subject name (SubjectID, Timepoint)
            report (pd.DataFrame): report dataframe

        Returns:
            Tuple[List[Union[DatasetStage, RowStage]], bool]: Stage to run, and wether it is done or not
        """
        could_run_stages = []
        for i, stage in enumerate(self.stages):
            could_run = False
            if isinstance(stage, RowStage):
                could_run = stage.could_run(subject, report)
            else:
                could_run = stage.could_run(report)

            if could_run:
                runnable_stage = self.stages[i]
                could_run_stages.append(runnable_stage)

        print(f"Possible next stages: {[stage.name for stage in could_run_stages]}")

        # TODO: split into a function
        if len(could_run_stages) == 1:
            stage = could_run_stages[0]
            is_last_subject = subject == report.index[-1]
            if isinstance(stage, DatasetStage) and not is_last_subject:
                # Only run dataset stages on the last subject, so all subjects can update
                # their state if needed before proceeding
                return None, False
            return stage, False

        # Handle errors
        # Either no stage can be executed (len(could_run_stages == 0))
        # or multiple stages can be executed (len(could_run_stages > 1))
        report_stage = self.__get_report_stage_to_run(subject, report)
        if report_stage is not None:
            print(f"Reported next stage: {report_stage.name}")

        # TODO: split into a function
        if len(could_run_stages) == 0:
            # Either the case processing was on-going but it's state is broken
            # or the next stage is a dataset stage, which means we're done with this one
            # or the case is done and no stage can nor should run
            # We can tell this by looking at the report
            is_done = self.__is_subject_done(subject, report)
            is_dset_stage = isinstance(report_stage, DatasetStage)
            if is_done or is_dset_stage:
                return None, True
            else:
                return None, False
        # TODO: split into a function
        else:
            # Multiple stages could run. Remove ambiguity by
            # syncing with the report
            if report_stage in could_run_stages:
                return report_stage, False

            return could_run_stages[0], False

    def run(self, report: DataFrame, report_path: str):
        # cleanup the trash at the very beginning
        cleanup_storage(self.trash_folders)

        # The init stage always has to be executed
        report, _ = self.init_stage.execute(report)
        write_report(report, report_path)

        invalid_subjects = self.__invalid_subjects()

        should_loop = True
        should_stop = False
        while should_loop:

            # Since we could have row and dataset stages interwoven, we want
            # to make sure we continue processing subjects until nothing new has happened.
            # This means we can resume a given subject and its row stages even after a dataset stage
            prev_status = report["status"].copy()
            subjects = list(report.index)
            subjects_loop = tqdm(subjects)

            for subject in subjects_loop:
                report, should_stop = self.process_subject(
                    subject, report, report_path, subjects_loop
                )

                if should_stop:
                    break

                # If a new invalid subject is identified, start over
                new_invalid_subjects = self.__invalid_subjects()
                if invalid_subjects != new_invalid_subjects:
                    invalid_subjects = new_invalid_subjects
                    # We're going to restart the subjects loop
                    break

            # Check for report differences. If there are, rerun the loop
            should_loop = any(report["status"] != prev_status) and not should_stop

        if self.__is_done(report):
            cleanup_folders = self.staging_folders + self.trash_folders
            cleanup_storage(cleanup_folders)

    def process_subject(
        self, subject: Union[int, str], report: DataFrame, report_path: str, pbar: tqdm
    ):
        should_stop = False
        while True:
            # Check if subject has been invalidated
            invalid_subjects = self.__invalid_subjects()
            if subject in invalid_subjects:
                break

            # Filter out invalid subjects
            working_report = report[~report.index.isin(invalid_subjects)].copy()

            print(f"Determining next stage for {subject}", flush=True)
            stage, done = self.determine_next_stage(subject, working_report)
            if stage is not None:
                print(f"Next stage for {subject}: {stage.name}", flush=True)

            if done:
                print(f"Subject {subject} is Done", flush=True)
                break

            try:
                working_report, successful = self.run_stage(
                    stage, subject, working_report, pbar
                )
            except Exception:
                # TODO: The superclass could be in charge of catching the error, reporting it and cleaning up
                # and raise the exception again to be caught here
                working_report = self.__report_unhandled_exception(
                    stage, subject, working_report
                )
                print(traceback.format_exc())
                successful = False

            report.update(working_report)
            write_report(report, report_path)

            if not successful:
                # Send back a signal that a dset stage failed
                if isinstance(stage, DatasetStage):
                    should_stop = True
                break

        return report, should_stop

    def run_stage(self, stage, subject, report, pbar):
        successful = False
        if isinstance(stage, RowStage):
            pbar.set_description(f"{subject} | {stage.name}")
            report, successful = stage.execute(subject, report)
        elif isinstance(stage, DatasetStage):
            pbar.set_description(f"{stage.name}")
            report, successful = stage.execute(report)

        return report, successful

    def __report_unhandled_exception(
        self,
        stage: Stage,
        subject: Union[int, str],
        report: DataFrame,
    ):
        # Assign a special status code for unhandled errors, associated
        # to the stage status code
        status_code = -stage.status_code - 0.101
        name = f"{stage.name.upper().replace(' ', '_')}_UNHANDLED_ERROR"
        comment = traceback.format_exc()
        data_path = report.loc[subject]["data_path"]
        labels_path = report.loc[subject]["labels_path"]

        body = {
            "status": status_code,
            "status_name": name,
            "comment": comment,
            "data_path": data_path,
            "labels_path": labels_path,
        }

        report.loc[subject] = body

        return report
