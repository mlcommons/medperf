import logging
import os
import sys
import signal
import pandas as pd
from medperf.entities.dataset import Dataset
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import approval_prompt, dict_pretty_print
from medperf.exceptions import CommunicationError, ExecutionError, InvalidArgumentError
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ReportHandler(FileSystemEventHandler):
    def __init__(self, preparation_obj: "DataPreparation"):
        self.preparation = preparation_obj

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        preparation = self.preparation
        if event.src_path == preparation.report_path:
            report_metadata = {"execution_status": "running"}
            preparation.send_report(report_metadata)


class DataPreparation:
    @classmethod
    def run(cls, dataset_id: int, approve_sending_reports: bool = False):
        preparation = cls(dataset_id, approve_sending_reports)
        preparation.get_dataset()
        preparation.validate()
        preparation.get_prep_cube()
        preparation.setup_parameters()

        # TODO: make these more readable
        should_run_prepare = (
            not preparation.dataset.is_submitted_as_prepared()
            and not preparation.dataset.is_ready()
        )
        should_prompt_for_report_sending_approval = (
            should_run_prepare
            and not approve_sending_reports
            and not preparation.dataset.for_test
            and preparation.report_specified
        )
        if should_prompt_for_report_sending_approval:
            preparation.prompt_for_report_sending_approval()

        if should_run_prepare:
            preparation.run_prepare()

        with preparation.ui.interactive():
            preparation.run_sanity_check()
            preparation.run_statistics()

        preparation.mark_dataset_as_ready()

        return preparation.dataset.id

    def __init__(self, dataset_id: int, approve_sending_reports: bool):
        self.comms = config.comms
        self.ui = config.ui
        self.dataset_id = dataset_id
        self.dataset = None
        self.allow_sending_reports = approve_sending_reports
        self.latest_report_sent_at = None

    def get_dataset(self):
        self.dataset = Dataset.get(self.dataset_id)

    def validate(self):
        if self.dataset.state == "OPERATION":
            raise InvalidArgumentError("This dataset is in operation mode")

    def get_prep_cube(self):
        self.ui.text = "Retrieving data preparation cube"
        self.cube = Cube.get(self.dataset.data_preparation_mlcube)
        self.ui.print("> Preparation cube download complete")

    def setup_parameters(self):
        self.out_statistics_path = self.dataset.statistics_path
        self.out_datapath = self.dataset.data_path
        self.out_labelspath = self.dataset.labels_path
        self.report_path = self.dataset.report_path
        self.metadata_path = self.dataset.metadata_path
        self.raw_data_path, self.raw_labels_path = self.dataset.get_raw_paths()

        # Backwards compatibility. Run a cube as before if no report is specified
        self.report_specified = (
            self.cube.get_default_output("prepare", "report_file") is not None
        )
        # Backwards compatibility. Run a cube as before if no metadata is specified
        self.metadata_specified = (
            self.cube.get_default_output("prepare", "metadata_path") is not None
        )
        if not self.report_specified:
            self.allow_sending_reports = False

    def run_prepare(self):
        prepare_timeout = config.prepare_timeout

        prepare_params = {
            "data_path": self.raw_data_path,
            "labels_path": self.raw_labels_path,
            "output_path": self.out_datapath,
            "output_labels_path": self.out_labelspath,
        }

        observer = Observer()

        if self.metadata_specified:
            prepare_params["metadata_path"] = self.metadata_path

        if self.report_specified:
            prepare_params["report_file"] = self.report_path
            if self.allow_sending_reports:
                report_metadata = {"execution_status": "started"}
                self.send_report(report_metadata)

                def sigint_handler(sig, frame):
                    report_metadata = {"execution_status": "interrupted"}
                    self.send_report(report_metadata)
                    sys.exit(0)  # TODO: raise CleanExit instead?

                signal.signal(signal.SIGINT, sigint_handler)
                observer.schedule(ReportHandler(self), self.dataset.path)
                observer.start()

        self.ui.text = "Running preparation step..."
        try:
            with self.ui.interactive():
                self.cube.run(
                    task="prepare",
                    timeout=prepare_timeout,
                    **prepare_params,
                )
        except Exception as e:
            # Inform the server that a failure occured
            if self.allow_sending_reports:
                report_metadata = {"execution_status": "failed"}
                self.send_report(report_metadata)

            # Let the rest of the code handle the exception
            raise e

        self.ui.print("> Cube execution complete")

        # If any observer or signal was set, stop them
        signal.signal(signal.SIGINT, signal.default_int_handler)
        # TODO: perhaps should be .join() instead of stop?
        # maybe a report sending is in progress. Also, use this in sigint handling above
        observer.stop()

        # Send a last update to indicate preparation process finished
        # If the user didn't approve before, here we will ask again
        if self.allow_sending_reports:
            report_metadata = {"execution_status": "finished"}
            self.send_report(report_metadata)

    def run_sanity_check(self):
        sanity_check_timeout = config.sanity_check_timeout
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath

        # Specify parameters for the tasks
        sanity_params = {
            "data_path": out_datapath,
            "labels_path": out_labelspath,
        }

        self.ui.text = "Running sanity check..."
        try:
            self.cube.run(
                task="sanity_check",
                timeout=sanity_check_timeout,
                **sanity_params,
            )
        except ExecutionError:
            msg = "The sanity check process failed. This most probably means the data could not be completely prepared. "
            if self.report_specified:
                msg += (
                    f"You may want to check the status report at: {self.report_path} "
                )
            self.dataset.unmark_as_ready()
            raise ExecutionError(msg)
        self.ui.print("> Sanity checks complete")

    def run_statistics(self):
        statistics_timeout = config.statistics_timeout
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath

        statistics_params = {
            "data_path": out_datapath,
            "labels_path": out_labelspath,
            "output_path": self.out_statistics_path,
        }

        if self.metadata_specified:
            statistics_params["metadata_path"] = self.metadata_path

        self.ui.text = "Generating statistics..."

        try:
            self.cube.run(
                task="statistics",
                timeout=statistics_timeout,
                **statistics_params,
            )
        except ExecutionError as e:
            self.dataset.unmark_as_ready()
            raise e

        self.ui.print("> Statistics complete")

    def mark_dataset_as_ready(self):
        self.dataset.mark_as_ready()

    def __generate_report_dict(self):
        report_status_dict = {}

        if os.path.exists(self.report_path):
            with open(self.report_path, "r") as f:
                report_dict = yaml.safe_load(f)

            report = pd.DataFrame(report_dict)
            if "status_name" in report.keys():
                report_status = report.status_name.value_counts() / len(report)
                report_status_dict = report_status.round(3).to_dict()

        return report_status_dict

    def __generate_report_example(self):
        example_dict = {}
        if self.cube.params_path:
            with open(self.cube.params_path, "r") as f:
                parameters = yaml.safe_load(f) or {}

            if "medperf_report_stages" in parameters:
                # Generate example percentages
                stages = parameters["medperf_report_stages"]
                example_dict = {stage: 1 / len(stages) for stage in stages}

        if not example_dict:
            example_dict = {"<Stage1 Name>": 0.4, "<Stage2 Name>": 0.6}

        example = {
            "stats": example_dict,
            "execution_status": "[started][interrupted][running][failed][finished]",
        }

        return example

    def prompt_for_report_sending_approval(self):
        example = self.__generate_report_example()

        body = {
            "report_example": example,
        }

        msg = (
            "Do you approve the submission of the status report to the MedPerf Server?"
            + " This report will be visible by the benchmark owner and updated"
            + " with the latest status change throughout the preparation process."
            + " An example of the contents has been provided"
            + " [Y/n]"
        )

        dict_pretty_print(body)
        self.allow_sending_reports = approval_prompt(msg)

    def send_report(self, report_metadata):
        # if self.latest_report_sent_at is not None:
        #     if time() - self.latest_report_sent_at < 0.5:
        #         return
        # self.latest_report_sent_at = time()

        report_status_dict = self.__generate_report_dict()
        report = {"progress": report_status_dict, **report_metadata}

        body = {
            "report": report,
        }

        # TODO: it should have retries, perhaps?
        # TODO: modify this piece of code after merging the `entity edit` PR
        try:
            config.comms.update_dataset(self.dataset.id, body)
        except CommunicationError as e:
            # print warning?
            logging.error(str(e))
            return
        self.dataset.report = report
        self.dataset.write()
