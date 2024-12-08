import os
from medperf.entities.dataset import Dataset
from medperf.utils import (
    untar,
    move_folder,
    copy_file,
    remove_path,
    create_folders,
)
import medperf.config as config
from medperf.exceptions import ExecutionError, InvalidArgumentError
import yaml


class ImportDataset:
    @classmethod
    def run(cls, dataset_id: str, input_path: str, raw_data_path):
        import_dataset = cls(dataset_id, input_path, raw_data_path)
        import_dataset.validate_input()
        import_dataset.untar_files()
        import_dataset.validate()
        import_dataset.prepare()
        import_dataset.prepare_tarfiles()
        import_dataset.process_tarfiles()

    def __init__(self, dataset_id: str, input_path: str, raw_data_path):
        self.dataset_id = dataset_id
        self.input_path = input_path
        self.dataset = Dataset.get(self.dataset_id)
        self.dataset_storage = self.dataset.get_storage_path()
        self.dataset_path = os.path.join(self.dataset_storage, self.dataset_id)
        self.raw_data_path = raw_data_path

    def prepare(self):
        if self.dataset.state == "DEVELOPMENT":
            self.raw_data_path = os.path.join(
                self.raw_data_path, config.dataset_backup_foldername + self.dataset_id
            )
            create_folders(self.raw_data_path)

    def validate_input(self):
        if not os.path.exists(self.input_path):
            raise InvalidArgumentError(f"File {self.input_path} doesn't exist.")
        if not os.path.isfile(self.input_path):
            raise InvalidArgumentError(f"{self.input_path} is not a file.")
        if self.dataset.state == "DEVELOPMENT" and (
            self.raw_data_path is None
            or not os.path.exists(self.raw_data_path)
            or os.path.isfile(self.raw_data_path)
        ):
            raise InvalidArgumentError(f"Folder {self.raw_data_path} doesn't exist.")

    def _validate_dataset(self):
        # Helper function to check if the dataset's files already exist
        dataset_folders = os.listdir(self.dataset_path)
        for folder in dataset_folders:
            if folder in [
                os.path.basename(self.dataset.data_path),
                os.path.basename(self.dataset.labels_path),
            ] and (
                os.listdir(self.dataset.data_path)
                or os.listdir(self.dataset.labels_path)
            ):
                raise ExecutionError(f"Dataset '{self.dataset_id}' already exists.")

    def validate(self):
        # Dataset backup will be invalid if:
        # - yaml file that defines backup folders, doesn't exist in the tar file.
        # - The user is trying to import a local dataset into the server (and vice versa)
        # - The dataset already exists (checking labels and data paths if already exists)
        # It'll also compare the imported dataset and the original dataset (IDs)

        # Checking main backup folder existance
        if config.dataset_backup_foldername not in self.tarfiles:
            raise ExecutionError("Dataset backup is invalid")

        backup_config = os.path.join(self.tarfiles, config.backup_config_filename)
        tarfiles_names = os.listdir(self.tarfiles)

        # Checking yaml file existance
        if not os.path.exists(backup_config):
            raise ExecutionError("Dataset backup is invalid, config file doesn't exist")

        self.tarfiles = [os.path.join(self.tarfiles, file) for file in tarfiles_names]
        with open(backup_config) as f:
            self.paths = yaml.safe_load(f)
        print(self.paths)
        # Checks if yaml file paths are valid
        if self.paths["dataset"] not in tarfiles_names:
            raise ExecutionError("Dataset backup is invalid, dataset folders not found")

        # Checks if yaml file paths are valid for development datasets
        if self.dataset.state == "DEVELOPMENT" and (
            self.paths["data"] not in tarfiles_names
            or self.paths["labels"] not in tarfiles_names
        ):
            raise ExecutionError("Dataset backup is invalid, config file is invalid")

        self._validate_dataset()

        # Check if the dataset's ID being imported matches the one in the backup
        if self.dataset_id != self.paths["dataset"]:
            msg = "Cannot import dataset '{}' data to dataset '{}'"
            msg = msg.format(self.paths["dataset"], self.dataset_id)
            raise InvalidArgumentError(msg)

        # Check if the current profile's server matches the one in the backup
        if self.paths["server"] != config.server:
            if self.paths["server"] == "localhost_8000":
                raise ExecutionError(
                    "Cannot import local dataset backup to remote server!"
                )
            raise ExecutionError("Cannot remote dataset backup to local server!")

        # TODO: Add more checks (later) compraing dataset generated_uid and so

    def prepare_tarfiles(self):
        for file in self.tarfiles:
            if ".yaml" in os.path.basename(file):
                self.yaml_file = file
            elif os.path.basename(file) == self.dataset_id:
                self.dataset_folder = file
                self.tarfiles.remove(file)

    def process_tarfiles(self):
        # Moves extarcted folders from medperf tmp path into the right destinations.
        # Moves raw data paths only if the dataset is in development.

        remove_path(self.dataset_path)
        remove_path(self.yaml_file)

        move_folder(self.dataset_folder, self.dataset_storage)
        self.dataset.set_raw_paths("", "")
        if self.dataset.state == "DEVELOPMENT":
            for folder in self.tarfiles:
                if os.path.basename(folder) == self.paths["data"]:
                    move_folder(folder, self.raw_data_path)
                elif os.path.basename(folder) == self.paths["labels"]:
                    move_folder(folder, self.raw_data_path)
            raw_data_path = os.path.join(self.raw_data_path, self.paths["data"])
            raw_labels_path = os.path.join(self.raw_data_path, self.paths["labels"])
            self.dataset.set_raw_paths(raw_data_path, raw_labels_path)

    def untar_files(self):
        input_filename = os.path.basename(self.input_path)
        tmp_input_path = os.path.join(config.tmp_folder, input_filename)
        copy_file(self.input_path, tmp_input_path)
        config.tmp_paths.append(tmp_input_path)
        self.tarfiles = untar(tmp_input_path, remove=False)
        self.tarfiles = os.path.join(
            self.tarfiles, config.dataset_backup_foldername + self.dataset_id
        )
        config.tmp_paths.append(self.tarfiles)
