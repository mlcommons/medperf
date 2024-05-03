import os
from pathlib import Path
import shutil
from medperf.entities.dataset import Dataset
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    approval_prompt,
    dict_pretty_print,
    get_folders_hash,
    remove_path,
)
from medperf.exceptions import CleanExit, InvalidArgumentError


class DataCreation:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        prep_cube_uid: int,
        data_path: str,
        labels_path: str,
        metadata_path: str = None,
        name: str = None,
        description: str = None,
        location: str = None,
        approved: bool = False,
        submit_as_prepared: bool = False,
        for_test: bool = False,
    ):
        preparation = cls(
            benchmark_uid,
            prep_cube_uid,
            data_path,
            labels_path,
            metadata_path,
            name,
            description,
            location,
            approved,
            submit_as_prepared,
            for_test,
        )
        preparation.validate()
        preparation.validate_prep_cube()
        preparation.create_dataset_object()
        if submit_as_prepared:
            preparation.make_dataset_prepared()
        updated_dataset_dict = preparation.upload()
        preparation.to_permanent_path(updated_dataset_dict)
        preparation.write(updated_dataset_dict)

        return updated_dataset_dict["id"]

    def __init__(
        self,
        benchmark_uid: int,
        prep_cube_uid: int,
        data_path: str,
        labels_path: str,
        metadata_path: str,
        name: str,
        description: str,
        location: str,
        approved: bool,
        submit_as_prepared: bool,
        for_test: bool,
    ):
        self.ui = config.ui
        self.data_path = str(Path(data_path).resolve())
        self.labels_path = str(Path(labels_path).resolve())
        self.metadata_path = metadata_path
        self.name = name
        self.description = description
        self.location = location
        self.benchmark_uid = benchmark_uid
        self.prep_cube_uid = prep_cube_uid
        self.approved = approved
        self.submit_as_prepared = submit_as_prepared
        self.for_test = for_test

    def validate(self):
        if not os.path.exists(self.data_path):
            raise InvalidArgumentError("The provided data path doesn't exist")
        if not os.path.exists(self.labels_path):
            raise InvalidArgumentError("The provided labels path doesn't exist")

        if not self.submit_as_prepared and self.metadata_path:
            raise InvalidArgumentError(
                "metadata path should only be provided when the dataset is submitted as prepared"
            )
        if self.metadata_path:
            self.metadata_path = str(Path(self.metadata_path).resolve())
            if not os.path.exists(self.metadata_path):
                raise InvalidArgumentError("The provided metadata path doesn't exist")

        # TODO: should we check the prep mlcube and accordingly check if metadata path
        #       is required? For now, we will anyway create an empty metadata folder
        #       (in self.make_dataset_prepared)
        too_many_resources = self.benchmark_uid and self.prep_cube_uid
        no_resource = self.benchmark_uid is None and self.prep_cube_uid is None
        if no_resource or too_many_resources:
            raise InvalidArgumentError(
                "Must provide either a benchmark or a preparation mlcube"
            )

    def validate_prep_cube(self):
        if self.prep_cube_uid is None:
            benchmark = Benchmark.get(self.benchmark_uid)
            self.prep_cube_uid = benchmark.data_preparation_mlcube
        Cube.get(self.prep_cube_uid)

    def create_dataset_object(self):
        """generates dataset UIDs for both input path"""
        in_uid = get_folders_hash([self.data_path, self.labels_path])
        dataset = Dataset(
            name=self.name,
            description=self.description,
            location=self.location,
            data_preparation_mlcube=self.prep_cube_uid,
            input_data_hash=in_uid,
            generated_uid=in_uid,
            split_seed=0,
            generated_metadata={},
            state="DEVELOPMENT",
            submitted_as_prepared=self.submit_as_prepared,
            for_test=self.for_test,
        )
        dataset.write()
        config.tmp_paths.append(dataset.path)
        dataset.set_raw_paths(
            raw_data_path=self.data_path,
            raw_labels_path=self.labels_path,
        )
        self.dataset = dataset

    def make_dataset_prepared(self):
        shutil.copytree(self.data_path, self.dataset.data_path)
        shutil.copytree(self.labels_path, self.dataset.labels_path)
        if self.metadata_path:
            shutil.copytree(self.metadata_path, self.dataset.metadata_path)
        else:
            # Create an empty folder. The statistics logic should
            # also expect an empty folder to accommodate for users who
            # have prepared datasets with no the metadata information
            os.makedirs(self.dataset.metadata_path, exist_ok=True)

    def upload(self):
        submission_dict = self.dataset.todict()
        dict_pretty_print(submission_dict)
        msg = "Do you approve the registration of the presented data to MedPerf? [Y/n] "
        warning = (
            "Upon submission, your email address will be visible to the Data Preparation"
            + " Owner for traceability and debugging purposes."
            )
        self.ui.print_warning(warning)
        self.approved = self.approved or approval_prompt(msg)

        if self.approved:
            updated_body = self.dataset.upload()
            return updated_body

        raise CleanExit("Dataset submission operation cancelled")

    def to_permanent_path(self, updated_dataset_dict: dict):
        """Renames the temporary benchmark submission to a permanent one

        Args:
            bmk_dict (dict): dictionary containing updated information of the submitted benchmark
        """
        old_dataset_loc = self.dataset.path
        updated_dataset = Dataset(**updated_dataset_dict)
        new_dataset_loc = updated_dataset.path
        remove_path(new_dataset_loc)
        os.rename(old_dataset_loc, new_dataset_loc)

    def write(self, updated_dataset_dict):
        dataset = Dataset(**updated_dataset_dict)
        dataset.write()
