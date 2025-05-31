import logging
import os
import pandas as pd
from medperf.entities.dataset import Dataset
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import approval_prompt, dict_pretty_print
from medperf.exceptions import (
    CommunicationError,
    ExecutionError,
    InvalidArgumentError,
    CleanExit,
)
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer, Lock


class ReportHandler(FileSystemEventHandler):
    def __init__(self, preparation_obj: "DataPreparation"):
        self.preparation = preparation_obj
        self.timer = None

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        preparation = self.preparation
        if event.src_path == preparation.report_path:
            report_metadata = {"execution_status": "running"}
            if self.timer is None or not self.timer.is_alive():
                # NOTE: there is a very slight chance to miss a latest update
                #       if the calls of send_report in the main thread were
                #       interrupted. is_alive may return True while the send_report
                #       of the previous thread is being executed, which means the
                #       previous report contents are already being used.
                #       However, since we have the main thread's calls in case of
                #       failure, finishing, and keyboardinterrupt, we can assume
                #       the latest report contents will be sent anyway, unless
                #       one of those three finalizing actions were interrupted.
                #       (Note that this slight chance is not blocking/buggy).
                wait = config.wait_before_sending_reports
                self.timer = Timer(
                    wait, preparation.send_report, args=(report_metadata,)
                )
                self.timer.start()


class ReportSender:
    def __init__(self, preparation_obj: "DataPreparation"):
        self.preparation = preparation_obj

    def start(self):
        report_metadata = {"execution_status": "started"}
        self.preparation.send_report(report_metadata)

        self.observer = Observer()
        self.report_handler = ReportHandler(self.preparation)
        self.observer.schedule(self.report_handler, self.preparation.dataset.path)
        self.observer.start()

    def stop(self, execution_status):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        if self.report_handler.timer is not None:
            if self.report_handler.timer.is_alive():
                self.report_handler.timer.cancel()
                self.report_handler.timer.join()

        # Send an update to indicate preparation process finished/stopped
        report_metadata = {"execution_status": execution_status}
        self.preparation.send_report(report_metadata)


class DataPreparation:
    @classmethod
    def run(cls, dataset_id: int, approve_sending_reports: bool = False):
        preparation = cls(dataset_id, approve_sending_reports)
        preparation.get_dataset()
        preparation.validate()
        with preparation.ui.interactive():
            preparation.get_prep_cube()
        preparation.setup_parameters()

        # TODO: make these more readable
        if preparation.should_prompt_for_report_sending_approval():
            preparation.prompt_for_report_sending_approval()

        if preparation.should_run_prepare():
            with preparation.ui.interactive():
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
        self.allow_sending_reports = approve_sending_reports
        self.dataset = None
        self.cube = None
        self.out_statistics_path = None
        self.out_datapath = None
        self.out_labelspath = None
        self.report_path = None
        self.metadata_path = None
        self.raw_data_path = None
        self.raw_labels_path = None
        self.report_specified = None
        self.metadata_specified = None
        self._lock = Lock()

    def should_run_prepare(self):
        return not self.dataset.submitted_as_prepared and not self.dataset.is_ready()

    def should_prompt_for_report_sending_approval(self):
        return (
            self.should_run_prepare()
            and not self.allow_sending_reports
            and not self.dataset.for_test
            and self.report_specified
        )

    def get_dataset(self):
        self.dataset = Dataset.get(self.dataset_id)

    def validate(self):
        if self.dataset.state == "OPERATION":
            raise InvalidArgumentError("This dataset is in operation mode")

    def get_prep_cube(self):
        self.ui.text = (
            "Retrieving and setting up data preparation Container. "
            "This may take some time."
        )
        self.cube = Cube.get(self.dataset.data_preparation_mlcube)
        self.cube.download_run_files()
        self.ui.print("> Preparation container download complete")

    def setup_parameters(self):
        self.out_statistics_path = self.dataset.statistics_path
        self.out_datapath = self.dataset.data_path
        self.out_labelspath = self.dataset.labels_path
        self.report_path = self.dataset.report_path
        self.metadata_path = self.dataset.metadata_path
        self.raw_data_path, self.raw_labels_path = self.dataset.get_raw_paths()

        # Backwards compatibility. Run a cube as before if no report is specified
        self.report_specified = self.cube.is_report_specified()

        # Backwards compatibility. Run a cube as before if no metadata is specified
        self.metadata_specified = self.cube.is_metadata_specified()

        if not self.report_specified:
            self.allow_sending_reports = False

    def run_prepare(self):
        report_sender = ReportSender(self)
        report_sender.start()

        prepare_mounts = {
            "data_path": self.raw_data_path,
            "labels_path": self.raw_labels_path,
            "output_path": self.out_datapath,
            "output_labels_path": self.out_labelspath,
        }
        if self.metadata_specified:
            prepare_mounts["metadata_path"] = self.metadata_path

        if self.report_specified:
            prepare_mounts["report_file"] = self.report_path

        self.ui.text = "Running preparation step..."
        try:
            with self.ui.interactive():
                self.cube.run(
                    task="prepare",
                    timeout=config.prepare_timeout,
                    mounts=prepare_mounts,
                )
        except Exception as e:
            # Inform the server that a failure occured
            report_sender.stop("failed")
            raise e
        except KeyboardInterrupt as e:
            # Inform the server that the process is interrupted
            report_sender.stop("interrupted")
            raise e

        self.ui.print("> Container execution complete")
        report_sender.stop("finished")

    def run_sanity_check(self):
        sanity_check_timeout = config.sanity_check_timeout
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath

        # Specify parameters for the tasks
        sanity_check_mounts = {
            "data_path": out_datapath,
            "labels_path": out_labelspath,
        }

        self.ui.text = "Running sanity check..."
        try:
            self.cube.run(
                task="sanity_check",
                timeout=sanity_check_timeout,
                mounts=sanity_check_mounts,
            )
        except ExecutionError:
            self.dataset.unmark_as_ready()
            if self.report_specified:
                msg = (
                    "The preprocessing stage finished executing, "
                    "but the data doesn't appear to be ready. "
                    "This most probably means you have outstanding tasks. "
                    "Please verify the status of your data by using the "
                    "monitoring tool."
                )
                self.ui.print_warning(msg)
                raise CleanExit(medperf_status_code=1)

            msg = "The sanity check process failed"
            raise ExecutionError(msg)
        self.ui.print("> Sanity checks complete")

    def run_statistics(self):
        statistics_timeout = config.statistics_timeout
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath

        statistics_mounts = {
            "data_path": out_datapath,
            "labels_path": out_labelspath,
            "output_path": self.out_statistics_path,
        }

        if self.metadata_specified:
            statistics_mounts["metadata_path"] = self.metadata_path

        self.ui.text = "Generating statistics..."

        try:
            self.cube.run(
                task="statistics",
                timeout=statistics_timeout,
                mounts=statistics_mounts,
            )
        except ExecutionError as e:
            self.dataset.unmark_as_ready()
            raise e

        with open(self.out_statistics_path) as f:
            stats = yaml.safe_load(f)

        if stats is None:
            self.dataset.unmark_as_ready()
            raise ExecutionError("Statistics file is empty.")

        self.ui.print("> Statistics complete")

    def mark_dataset_as_ready(self):
        self.dataset.mark_as_ready()

    def __generate_report_dict(self):
        report_status_dict = {}

        if os.path.exists(self.report_path):
            with open(self.report_path, "r") as f:
                report_dict = yaml.safe_load(f)

            # TODO: this specific logic with status is very tuned to the RANO. Hope we'd
            #  make it more general once
            report = pd.DataFrame(report_dict)
            if "status" in report.keys():
                report_status = report.status.value_counts() / len(report)
                report_status_dict = report_status.round(3).to_dict()
                report_status_dict = {
                    f"Stage {key}": str(val * 100) + "%"
                    for key, val in report_status_dict.items()
                }

        return report_status_dict

    def prompt_for_report_sending_approval(self):
        example = {
            "execution_status": "running",
            "progress": {
                "Stage 1": "40%",
                "Stage 3": "60%",
            },
        }

        msg = (
            "\n=================================================\n"
            + "During preparation, each subject of your dataset will undergo multiple"
            + " stages (For example, DICOM to NIFTI conversion stage, brain extraction stage)."
            + " MedPerf will generate a summary of the progress of the data preparation and"
            + " will send this summary to the MedPerf server.\nThis will happen multiple times"
            + " during the preparation process in order to facilitate the supervision of the"
            + " experiment. The summary will be only visible to the data preparation container owner."
            + "\nBelow is an example of this summary, which conveys that the current execution"
            + " status of your dataset preparation is actively running, and that 40% of your"
            + " dataset subjects have reached Stage 1, and that 60% of your dataset subjects"
            + " have reached Stage 3:"
        )
        config.ui.print(msg)
        dict_pretty_print(example)

        msg = (
            "\nYou can decide whether or not to send information about your dataset preparation"
            + "\nProgress. Keep in mind that information about the execution status of the pipeline"
            + "\nwill be sent regardless (whether the pipeline is running, finished or failed)"
            + "\nto identify issues with the preparation procedure. Do you approve the automatic"
            + "\nsubmission of summaries similar to the one above to the MedPerf Server throughout"
            + "\nthe preparation process?[Y/n]"
        )

        self.allow_sending_reports = approval_prompt(msg)

    def send_report(self, report_metadata):
        # Since we don't actually need concurrency, let's have
        # this logic under a lock (and prevent any possibly unforseen
        # problem, such as async dataset.write)
        with self._lock:
            return self._send_report(report_metadata)

    def _send_report(self, report_metadata):
        if self.dataset.for_test:
            # Test datasets don't have a registration on the server
            return
        report_status_dict = {}
        if self.allow_sending_reports:
            report_status_dict = self.__generate_report_dict()
        report = {"progress": report_status_dict, **report_metadata}
        if report == self.dataset.report:
            # Watchdog may trigger an event even if contents didn't change
            return

        body = {
            "report": report,
        }

        # TODO: it should have retries, perhaps?  NO, later
        # TODO: modify this piece of code after merging the `entity edit` PR
        try:
            config.comms.update_dataset(self.dataset.id, body)
        except CommunicationError as e:
            # print warning?
            logging.error(str(e))
            return
        self.dataset.report = report
        self.dataset.write()
