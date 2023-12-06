import logging
import os
import sys
import signal
from pathlib import Path
from medperf.entities.dataset import Dataset
from medperf.enums import Status
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.commands.report.submit import ReportRegistration
from medperf.utils import (
    remove_path,
    generate_tmp_path,
    get_folder_hash,
    storage_path,
)
from medperf.exceptions import InvalidArgumentError, ExecutionError
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ReportHandler(FileSystemEventHandler):
    def __init__(self, preparation_obj: "DataPreparation", submission_approved):
        self.preparation = preparation_obj
        self.submission_approved = submission_approved

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        preparation = self.preparation
        if event.src_path == preparation.report_path:
            in_data_hash = preparation.in_uid
            name = preparation.name
            desc = preparation.description
            loc = preparation.location
            prep_cube_uid = preparation.prep_cube_uid
            benchmark_uid = preparation.benchmark_uid
            summary_path = preparation.summary_path
            metadata = {"execution_status": "running"}

            ReportRegistration.run(
                in_data_hash,
                name,
                desc,
                loc,
                prep_cube_uid,
                benchmark_uid,
                metadata=metadata,
            )


class DataPreparation:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        prep_cube_uid: int,
        data_path: str,
        labels_path: str,
        run_test=False,
        name: str = None,
        description: str = None,
        location: str = None,
        summary_path: str = "",
    ):
        summary_path = os.path.join(summary_path, "summary.md")
        preparation = cls(
            benchmark_uid,
            prep_cube_uid,
            data_path,
            labels_path,
            summary_path,
            name,
            description,
            location,
            run_test,
        )
        preparation.validate()
        preparation.get_prep_cube()
        preparation.set_staging_parameters()

        # Run cube tasks
        # The prepare function handles interactivity from within
        preparation.run_prepare()

        with preparation.ui.interactive():
            preparation.run_sanity_check()
            preparation.run_statistics()

        preparation.get_statistics()
        preparation.generate_uids()
        preparation.to_permanent_path()
        preparation.write()

        return preparation.generated_uid

    def __init__(
        self,
        benchmark_uid: int,
        prep_cube_uid: int,
        data_path: str,
        labels_path: str,
        summary_path: str,
        name: str,
        description: str,
        location: str,
        run_test=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.data_path = str(Path(data_path).resolve())
        self.labels_path = str(Path(labels_path).resolve())
        self.summary_path = str(Path(summary_path).resolve())
        self.in_uid = get_folder_hash(self.data_path)
        self.out_statistics_path = generate_tmp_path()
        self.name = name
        self.description = description
        self.location = location
        self.run_test = run_test
        self.benchmark_uid = benchmark_uid
        self.prep_cube_uid = prep_cube_uid
        self.generated_uid = None
        self.approved = False
        self.report_uid = None

    def validate(self):
        if not os.path.exists(self.data_path):
            raise InvalidArgumentError("The provided data path doesn't exist")
        if not os.path.exists(self.labels_path):
            raise InvalidArgumentError("The provided labels path doesn't exist")

        too_many_resources = self.benchmark_uid and self.prep_cube_uid
        no_resource = self.benchmark_uid is None and self.prep_cube_uid is None
        if no_resource or too_many_resources:
            raise InvalidArgumentError(
                "Must provide either a benchmark or a preparation mlcube"
            )

    def get_prep_cube(self):
        cube_uid = self.prep_cube_uid
        if cube_uid is None:
            benchmark = Benchmark.get(self.benchmark_uid)
            cube_uid = benchmark.data_preparation_mlcube
            self.ui.print(f"Benchmark Data Preparation: {benchmark.name}")
        self.ui.text = "Retrieving data preparation cube"
        self.cube = Cube.get(cube_uid)
        self.ui.print("> Preparation cube download complete")

    def set_staging_parameters(self):
        staging_path = storage_path(config.staging_data_storage)
        out_path = os.path.join(staging_path, f"{self.name}_{self.cube.id}")
        self.out_path = out_path
        self.report_path = os.path.join(out_path, config.report_file)
        self.out_datapath = os.path.join(out_path, "data")
        self.out_labelspath = os.path.join(out_path, "labels")
        self.metadata_path = os.path.join(out_path, "metadata")

        # Check if labels_path is specified
        self.labels_specified = (
            self.cube.get_default_output("prepare", "output_labels_path") is not None
        )
        # Backwards compatibility. Run a cube as before if no report is specified
        self.report_specified = (
            self.cube.get_default_output("prepare", "report_file") is not None
        )
        # Backwards compatibility. Run a cube as before if no metadata is specified
        self.metadata_specified = (
            self.cube.get_default_output("prepare", "metadata_path") is not None
        )

        logging.debug(f"tmp data preparation output: {out_path}")
        logging.debug(f"tmp data statistics output: {self.out_statistics_path}")

    def run_prepare(self):
        prepare_timeout = config.prepare_timeout
        data_path = self.data_path
        labels_path = self.labels_path
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath
        out_report = self.report_path
        in_data_hash = self.in_uid
        name = self.name
        desc = self.description
        loc = self.location
        prep_cube_uid = self.prep_cube_uid
        benchmark_uid = self.benchmark_uid
        approved = False

        prepare_params = {
            "data_path": data_path,
            "labels_path": labels_path,
            "output_path": out_datapath,
            "output_labels_path": out_labelspath,
        }
        prepare_str_params = {
            "Ptasks.prepare.parameters.input.data_path.opts": "ro",
            "Ptasks.prepare.parameters.input.labels_path.opts": "ro",
        }

        def sigint_handler(sig, frame):
            metadata = {"execution_status": "interrupted"}
            ReportRegistration.run(
                in_data_hash,
                name,
                desc,
                loc,
                prep_cube_uid,
                benchmark_uid,
                metadata=metadata,
            )
            sys.exit(0)

        observer = Observer()

        if self.metadata_specified:
            prepare_params["metadata_path"] = self.metadata_path

        if self.report_specified:
            prepare_params["report_file"] = out_report
            metadata = {"execution_status": "started"}

            approved = ReportRegistration.run(
                in_data_hash,
                name,
                desc,
                loc,
                prep_cube_uid,
                benchmark_uid,
                metadata=metadata,
            )

            if approved:
                signal.signal(signal.SIGINT, sigint_handler)
            observer.schedule(ReportHandler(self, approved), self.out_path)
            observer.start()

        self.ui.text = "Running preparation step..."
        try:
            with self.ui.interactive():
                self.cube.run(
                    task="prepare",
                    string_params=prepare_str_params,
                    timeout=prepare_timeout,
                    **prepare_params,
                )
        except Exception as e:
            # Inform the server that a failure occured
            metadata = {"execution_status": "failed"}
            if approved:
                ReportRegistration.run(
                    in_data_hash,
                    name,
                    desc,
                    loc,
                    prep_cube_uid,
                    benchmark_uid,
                    metadata=metadata,
                )

            # Let the rest of the code handle the exception
            raise e

        self.ui.print("> Cube execution complete")

        # If any observer or signal was set, stop them
        signal.signal(signal.SIGINT, signal.default_int_handler)
        observer.stop()

        # Send a last update to indicate preparation process finished
        # If the user didn't approve before, here we will ask again
        metadata = {"execution_status": "finished"}
        ReportRegistration.run(
            in_data_hash,
            name,
            desc,
            loc,
            prep_cube_uid,
            benchmark_uid,
            metadata=metadata,
        )

    def run_sanity_check(self):
        sanity_check_timeout = config.sanity_check_timeout
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath
        out_report = self.report_path

        # Specify parameters for the tasks
        sanity_params = {
            "data_path": out_datapath,
        }
        sanity_str_params = {
            "Ptasks.sanity_check.parameters.input.data_path.opts": "ro",
        }

        if self.labels_specified:
            # Add the labels parameter
            sanity_params["labels_path"] = out_labelspath

        if self.metadata_specified:
            sanity_params["metadata_path"] = self.metadata_path
            sanity_params[
                "Ptasks.sanity_check.parameters.input.metadata_paths.opts"
            ] = "ro"

        if self.report_specified:
            sanity_params["report_file"] = out_report
            sanity_str_params[
                "Ptasks.sanity_check.parameters.input.report_file.opts"
            ] = "ro"

        self.ui.text = "Running sanity check..."
        try:
            self.cube.run(
                task="sanity_check",
                string_params=sanity_str_params,
                timeout=sanity_check_timeout,
                **sanity_params,
            )
        except ExecutionError:
            msg = "The sanity check process failed. This most probably means the data could not be completely prepared. "
            if self.report_specified:
                msg += (
                    f"You may want to check the status report at: {self.summary_path} "
                )
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
        statistics_str_params = {
            "Ptasks.statistics.parameters.input.data_path.opts": "ro"
        }

        if self.metadata_specified:
            statistics_params["metadata_path"] = self.metadata_path
            statistics_params[
                "Ptasks.statistics.parameters.input.metadata_path.opts"
            ] = "ro"

        self.ui.text = "Generating statistics..."

        self.cube.run(
            task="statistics",
            string_params=statistics_str_params,
            timeout=statistics_timeout,
            **statistics_params,
        )
        self.ui.print("> Statistics complete")

    def get_statistics(self):
        with open(self.out_statistics_path, "r") as f:
            stats = yaml.safe_load(f)
        self.generated_metadata = stats

    def generate_uids(self):
        """Auto-generates dataset UIDs for both input and output paths"""
        self.in_uid = get_folder_hash(self.data_path)
        self.generated_uid = get_folder_hash(self.out_datapath)

    def to_permanent_path(self) -> str:
        """Renames the temporary data folder to permanent one using the hash of
        the registration file
        """
        new_path = os.path.join(storage_path(config.data_storage), self.generated_uid)
        remove_path(new_path)
        os.rename(self.out_path, new_path)
        self.out_path = new_path

    def todict(self) -> dict:
        """Dictionary representation of the dataset

        Returns:
            dict: dictionary containing information pertaining the dataset.
        """
        return {
            "id": None,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "data_preparation_mlcube": self.cube.identifier,
            "input_data_hash": self.in_uid,
            "generated_uid": self.generated_uid,
            "split_seed": 0,  # Currently this is not used
            "generated_metadata": self.generated_metadata,
            "status": Status.PENDING.value,  # not in the server
            "state": "OPERATION",
            "for_test": self.run_test,  # not in the server (OK)
        }

    def write(self) -> str:
        """Writes the registration into disk
        Args:
            filename (str, optional): name of the file. Defaults to config.reg_file.
        """
        dataset_dict = self.todict()
        dataset = Dataset(**dataset_dict)
        dataset.write()
