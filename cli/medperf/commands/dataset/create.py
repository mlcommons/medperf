import logging
import os
from pathlib import Path
from medperf.entities.dataset import Dataset
from medperf.enums import Status
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    remove_path,
    generate_tmp_path,
    get_folder_sha1,
    storage_path,
    dict_pretty_print,
    approval_prompt,
    pretty_error,
)
from medperf.exceptions import InvalidArgumentError, ExecutionError
import yaml


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
    ):
        preparation = cls(
            benchmark_uid,
            prep_cube_uid,
            data_path,
            labels_path,
            name,
            description,
            location,
            run_test,
        )
        preparation.validate()
        with preparation.ui.interactive():
            preparation.get_prep_cube()
            preparation.set_staging_parameters()

            # Run cube tasks
            preparation.run_prepare()
        if benchmark_uid:
            preparation.submit_report()
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
        name: str,
        description: str,
        location: str,
        run_test=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.data_path = str(Path(data_path).resolve())
        self.labels_path = str(Path(labels_path).resolve())
        self.in_uid = get_folder_sha1(self.data_path)
        self.out_statistics_path = generate_tmp_path()
        self.name = name
        self.description = description
        self.location = location
        self.labels_specified = False
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
        self.ui.text = f"Retrieving data preparation cube: '{cube_uid}'"
        self.cube = Cube.get(cube_uid)
        self.ui.print("> Preparation cube download complete")

    def set_staging_parameters(self):
        staging_path = storage_path(config.staging_data_storage)
        out_path = os.path.join(staging_path, f"{self.in_uid}_{self.cube.id}")
        self.out_path = out_path
        self.report_path = os.path.join(out_path, config.report_file)
        self.report_metadata_path = os.path.join(out_path, config.report_metadata_file)
        self.out_datapath = os.path.join(out_path, "data")
        self.out_labelspath = os.path.join(out_path, "labels")

        if os.path.exists(self.report_metadata_path):
            # The report has already been submitted
            # Retrieve the report server ID
            with open(self.report_metadata_path, "r") as f:
                report_metadata = yaml.safe_load(f)
            self.report_uid = report_metadata["id"]
            self.approved = True

        # Check if labels_path is specified
        self.labels_specified = (
            self.cube.get_default_output("prepare", "output_labels_path") is not None
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

        prepare_params = {
            "data_path": data_path,
            "labels_path": labels_path,
            "output_path": out_datapath,
            "report_file": out_report,
        }
        prepare_str_params = {
            "Ptasks.prepare.parameters.input.data_path.opts": "ro",
            "Ptasks.prepare.parameters.input.labels_path.opts": "ro",
        }

        if self.labels_specified:
            prepare_params["output_labels_path"] = out_labelspath

        self.ui.text = "Running preparation step..."
        self.cube.run(
            task="prepare",
            string_params=prepare_str_params,
            timeout=prepare_timeout,
            **prepare_params,
        )
        self.ui.print("> Cube execution complete")

    def run_sanity_check(self):
        sanity_check_timeout = config.sanity_check_timeout
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath
        out_report = self.report_path

        # Specify parameters for the tasks
        sanity_params = {
            "data_path": out_datapath,
            "report_file": out_report,
        }
        sanity_str_params = {
            "Ptasks.sanity_check.parameters.input.data_path.opts": "ro",
            "Ptasks.sanity_check.parameters.input.report_file.opts": "ro",
        }

        if self.labels_specified:
            # Add the labels parameter
            sanity_params["labels_path"] = out_labelspath

        self.ui.text = "Running sanity check..."
        try:
            self.cube.run(
                task="sanity_check",
                string_params=sanity_str_params,
                timeout=sanity_check_timeout,
                **sanity_params,
            )
        except ExecutionError:
            msg = (
                "The sanity check process failed. This most probably means the data could not be completely prepared. "
                + f"You may want to check the status report at: {self.report_path}"
            )
            raise ExecutionError(msg)
        self.ui.print("> Sanity checks complete")

    def run_statistics(self):
        statistics_timeout = config.statistics_timeout
        out_datapath = self.out_datapath

        statistics_params = {
            "data_path": out_datapath,
            "output_path": self.out_statistics_path,
        }
        statistics_str_params = {
            "Ptasks.statistics.parameters.input.data_path.opts": "ro"
        }

        self.ui.text = "Generating statistics..."

        self.cube.run(
            task="statistics",
            string_params=statistics_str_params,
            timeout=statistics_timeout,
            **statistics_params,
        )
        self.ui.print("> Statistics complete")

    # TODO: this could be a separate commmand, and be executed inside this workflow
    # That would be more inline with our previous code structure
    def submit_report(self):
        with open(self.report_path, "r") as f:
            report = yaml.safe_load(f)

        if self.report_uid is None:
            self.request_submission_approval()

        if not self.approved:
            config.ui.print("Report submission cancelled")
            return

        config.ui.print("Uploading report")
        # TODO: if we have a path to the case file, remove it from the submisison body
        # example:
        # del report["path"]
        body = {
            "benchmark_id": self.benchmark_uid,
            "dataset_input_hash": self.in_uid,
            "report": report,
        }

        if self.report_uid is not None:
            report_metadata = config.comms.update_report(self.report_uid, body)
        else:
            report_metadata = config.comms.upload_report(body)

        with open(self.report_metadata_path, "w") as f:
            yaml.dump(report_metadata, f)

    def request_submission_approval(self):
        with open(self.report_path, "r") as f:
            report = yaml.safe_load(f)
        dict_pretty_print(report)
        msg = (
            "Do you approve the submission of the status report to the MedPerf Server?"
            + " This report will be visible by the benchmark owner and updated in subsequent calls"
            + " [Y/n]"
        )

        self.approved = self.approved or approval_prompt(msg)

    def get_statistics(self):
        with open(self.out_statistics_path, "r") as f:
            stats = yaml.safe_load(f)
        self.generated_metadata = stats

    def generate_uids(self):
        """Auto-generates dataset UIDs for both input and output paths"""
        self.in_uid = get_folder_sha1(self.data_path)
        self.generated_uid = get_folder_sha1(self.out_datapath)

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
            "separate_labels": self.labels_specified,  # not in the server
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
