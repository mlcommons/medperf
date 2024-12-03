import logging
import os
from medperf.entities.dataset import Dataset
from medperf.utils import (
    untar,
    tar,
    move_folder,
    approval_prompt,
    create_folders,
    copy_file,
    remove_path,
)
import medperf.config as config
from medperf.exceptions import CleanExit, ExecutionError
import yaml


class ImportDataset:
    @classmethod
    def run(cls, dataset_id: str, input_path: str):
        preparation = cls(dataset_id, input_path)
        if preparation.dataset.state == "DEVELOPMENT":
            preparation.prepare()

        preparation.untar_files()
        preparation.prepare_tarfiles()
        preparation.validate()
        preparation.process_tarfiles()

    def __init__(self, dataset_id: str, input_path: str):
        self.dataset_id = dataset_id
        self.input_path = input_path
        self.dataset = Dataset.get(self.dataset_id)
        self.dataset_path = os.path.join(
            self.dataset.get_storage_path(), self.dataset_id
        )

    def _check_paths(self):
        # Checks if the entered paths already contains the folders that are extacted (raw data)
        # Prompts user if it'll overwrite the folders if exists.
        new_raw_data_path = os.path.join(self.new_data_path, self.paths["data"])
        new_raw_labels_path = os.path.join(self.new_data_path, self.paths["labels"])
        if os.path.exists(new_raw_data_path):
            if approval_prompt(
                f"Folder {new_raw_data_path} already exists, do you want to overwrite it? [Y/n]"
            ):
                remove_path(new_raw_data_path)

            else:
                raise CleanExit("Moving aborted.")
        if os.path.exists(new_raw_labels_path):
            if approval_prompt(
                f"Folder {new_raw_labels_path} already exists, do you want to overwrite it? [Y/n]"
            ):
                remove_path(new_raw_labels_path)
            else:
                raise CleanExit("Moving aborted.")

    def prepare(self):
        # Prompting user to enter the desired raw data&labels path (where it should be saved)
        # Then sets the raw paths for the dataset.
        logging.info("Prompting for user's input raw data path")
        ui = config.ui
        data_path = labels_path = None
        while (
            data_path is None
            or labels_path is None
            or not os.path.exists(data_path)
            or not os.path.exists(labels_path)
        ):
            data_path = ui.prompt(
                "Please enter the raw_data_path to be saved: "
            ).strip()
            if not os.path.exists(data_path):
                if approval_prompt(
                    f"{data_path} doesn't exist, do you want to create that folder? [Y/n]"
                ):
                    try:
                        create_folders(data_path)
                    except PermissionError as e:
                        raise ExecutionError(
                            f"Cannot create folder(s) at {data_path}, " + e.strerror
                        )
                else:
                    raise CleanExit(f"Folder creation at {data_path} Aborted.")
            labels_path = ui.prompt(
                "Please enter the raw_labels_path to be saved: "
            ).strip()
            if not os.path.exists(data_path):
                if approval_prompt(
                    f"{labels_path} doesn't exist, do you want to create that folder? [Y/n]"
                ):
                    try:
                        create_folders(labels_path)
                    except PermissionError as e:
                        raise ExecutionError(
                            f"Cannot create folder(s) at {labels_path}, " + e.strerror
                        )
                else:
                    raise CleanExit(f"Folder creation at {labels_path} Aborted.")

        self.dataset.set_raw_paths(data_path, labels_path)
        self.new_data_path, self.new_lables_path = self.dataset.get_raw_paths()
        logging.info(f"User entered raw_data_path: {data_path}")
        logging.info(f"User entered raw_labels_path: {labels_path}")

    def validate(self):
        # Dataset backup will be invalid if:
        # - paths.yaml file doesn't exist in the tar file.
        # - Tar file should contain 2 files for Operational datasets,
        #    or 4 files for Development ones.
        # - The user is trying to import a local dataset into the server (and vice versa)
        # - The dataset already exists (checking labels and data paths if already exists)
        # It'll also compare the imported dataset and the original dataset (IDs)
        if len(self.tarfiles) < 2 or "paths.yaml" not in self.tarfiles:
            raise ExecutionError("Dataset backup is invalid")
        self.dataset_folder = os.path.join(
            self.dataset.get_storage_path(), self.dataset_id
        )
        dataset_folders = os.listdir(self.dataset_folder)
        for folder in dataset_folders:
            if folder in [
                os.path.basename(self.dataset.data_path),
                os.path.basename(self.dataset.labels_path),
            ] and (
                os.listdir(self.dataset.data_path)
                or os.listdir(self.dataset.labels_path)
            ):
                raise ExecutionError(f"Dataset '{self.dataset_id}' already exists.")

        if self.dataset_id != self.paths["dataset"]:
            msg = "Cannot import dataset '{}' data to dataset '{}'"
            raise ExecutionError(msg.format(self.paths["dataset"], self.dataset_id))

        dataset_servername = os.path.basename(self.dataset.get_storage_path())
        servername = self.paths["server"]
        if servername != dataset_servername:
            if servername == "localhost_8000":
                raise ExecutionError("Cannot import local data to remote server!")
            else:
                raise ExecutionError("Cannot remote data to local server!")

        if self.dataset.state == "DEVELOPMENT":
            if len(self.tarfiles) != 4:
                raise ExecutionError("Dataset backup is invalid")
        # TODO: Add more checks (later) compraing dataset generated_uid and so

    def prepare_tarfiles(self):
        # Reads the yaml file that'll contain folders names, and server type.
        # Prepares tmp paths so they'll be cleaned up.
        for file in self.tarfiles:
            config.tmp_paths.append(os.path.join(config.tmp_folder, file))
        with open(os.path.join(config.tmp_folder, "paths.yaml")) as f:
            self.paths = yaml.safe_load(f)

    def process_tarfiles(self):
        # Moves extarcted folders from medperf tmp path into the right destinations.
        # Moves raw data paths only if the dataset is in development.
        self._check_paths()
        remove_path(self.dataset_path)
        move_folder(
            os.path.join(config.tmp_folder, self.paths["dataset"]),
            self.dataset.get_storage_path(),
        )
        if self.dataset.state == "DEVELOPMENT":
            move_folder(
                os.path.join(config.tmp_folder, self.paths["data"]),
                self.new_data_path,
            )
            move_folder(
                os.path.join(config.tmp_folder, self.paths["labels"]),
                self.new_lables_path,
            )

    def untar_files(self):
        input_filename = os.path.basename(self.input_path)
        tmp_input_path = os.path.join(config.tmp_folder, input_filename)
        copy_file(self.input_path, tmp_input_path)
        self.tarfiles = os.listdir(untar(tmp_input_path))


class ExportDataset:
    @classmethod
    def run(cls, dataset_id: str, output_path: str):
        preparation = cls(dataset_id, output_path)
        preparation.prepare()
        preparation.create_tar()

    def __init__(self, dataset_id: str, output_path: str):
        self.dataset_id = dataset_id
        self.output_path = os.path.join(output_path, dataset_id) + ".gz"
        self.folders_paths = []
        self.dataset = Dataset.get(self.dataset_id)

    def prepare(self):
        # Gets server name to be added in paths.yaml for comparing between local and remote servers
        # which will save folders names (what each one points to.
        servername = os.path.basename(self.dataset.get_storage_path())
        self.folders_paths.append(
            os.path.join(self.dataset.get_storage_path(), self.dataset_id)
        )
        paths = {"server": servername, "dataset": self.dataset_id}
        # If the dataset is in development, it'll need the raw paths as well.
        if self.dataset.state == "DEVELOPMENT":
            raw_data_paths = self.dataset.get_raw_paths()
            if not raw_data_paths:
                raise ExecutionError("Cannot find raw data paths")
            for folder in self.dataset.get_raw_paths():
                if not os.path.exists(folder):
                    raise ExecutionError(f"Cannot find raw data paths at '{folder}'")
                self.folders_paths.append(folder)
            data_path, labels_path = self.dataset.get_raw_paths()
            paths["data"] = os.path.basename(data_path)
            paths["labels"] = os.path.basename(labels_path)
        paths_path = os.path.join(
            config.tmp_folder, "paths.yaml"
        )  # maybe add paths.yaml in config.py?
        # paths.yaml will be created in medperf tmp directory
        with open(paths_path, "w") as f:
            yaml.dump(paths, f)
        self.folders_paths.append(paths_path)
        config.tmp_paths.append(paths_path)

    def create_tar(self):
        tar(self.output_path, self.folders_paths)
