import os
from medperf.entities.dataset import Dataset
from medperf.utils import generate_tmp_path, untar, move_folder, remove_path
import medperf.config as config
from medperf.exceptions import ExecutionError, InvalidArgumentError
import yaml


class ImportDataset:
    @classmethod
    def run(cls, dataset_id: str, input_path: str, raw_data_path: str):
        import_dataset = cls(dataset_id, input_path, raw_data_path)
        import_dataset.validate_input()
        import_dataset.untar_files()
        import_dataset.validate()
        import_dataset.process_tarfiles()

    def __init__(self, dataset_id: str, input_path: str, raw_data_path: str):
        self.dataset_id = dataset_id
        self.input_path = os.path.realpath(input_path)
        self.dataset = Dataset.get(self.dataset_id)
        self.raw_data_path = raw_data_path
        if raw_data_path is not None:
            self.raw_data_path = os.path.realpath(raw_data_path)

    def validate_input(self):
        # The input archive file should exist and be a file
        if not os.path.exists(self.input_path):
            raise InvalidArgumentError(f"File {self.input_path} doesn't exist.")
        if not os.path.isfile(self.input_path):
            raise InvalidArgumentError(f"{self.input_path} is not a file.")

        # raw_data_path should be provided if the imported dataset is in dev
        if self.dataset.state == "DEVELOPMENT" and (
            self.raw_data_path is None
            or os.path.isfile(self.raw_data_path)
            or (os.path.exists(self.raw_data_path) and os.listdir(self.raw_data_path))
        ):
            raise InvalidArgumentError(
                "Output raw data path must be specified and, the directory should be empty or does not exist."
            )

    def untar_files(self):
        extracted_path = generate_tmp_path()
        os.makedirs(extracted_path, exist_ok=True)
        self.tarfiles = untar(self.input_path, remove=False, extract_to=extracted_path)

    def _validate_archive_config(self, archive_config):
        archive_dataset_id = archive_config.get("dataset")
        archive_server = archive_config.get("server")
        archive_raw_data = archive_config.get("raw_data")
        archive_raw_labels = archive_config.get("raw_labels")

        if archive_dataset_id is None:
            raise InvalidArgumentError("Invalid archive config: dataset key not found")

        if archive_server is None:
            raise InvalidArgumentError("Invalid archive config: server key not found")

        if self.dataset.state == "DEVELOPMENT" and (
            archive_raw_data is None or archive_raw_labels is None
        ):
            raise InvalidArgumentError(
                "Invalid archive config: raw data keys not found"
            )

        # Check if the dataset's ID being imported matches the one in the archive
        if str(self.dataset_id) != str(archive_dataset_id):
            msg = "The archive dataset is '{}' while specified dataset is '{}'"
            msg = msg.format(archive_dataset_id, self.dataset_id)
            raise InvalidArgumentError(msg)

        # Check if the current profile's server matches the one in the archive
        if archive_server != config.server:
            raise InvalidArgumentError("Dataset export was done for a different server")

    def validate(self):
        # Dataset archive will be invalid if:
        # - yaml file that defines archive folders, doesn't exist in the tar file.
        # - The user is trying to import a local dataset into the server (and vice versa)
        # - The dataset already exists (checking labels and data paths if already exists)
        # It'll also compare the imported dataset and the original dataset (IDs)
        root_archive_folder = self.tarfiles

        # Checking yaml file existance
        archive_config = os.path.join(
            root_archive_folder, config.archive_config_filename
        )
        if not os.path.exists(archive_config):
            raise ExecutionError(
                "Dataset archive is invalid, config file doesn't exist"
            )
        with open(archive_config) as f:
            archive_config = yaml.safe_load(f)

        # validate config
        self._validate_archive_config(archive_config)

        # validate files/folders existence
        archive_prepared_dataset_path = os.path.join(
            root_archive_folder, str(self.dataset_id)
        )
        if not os.path.exists(archive_prepared_dataset_path):
            raise ExecutionError("No prepared dataset in archive")

        if os.path.exists(self.dataset.data_path) or os.path.exists(
            self.dataset.labels_path
        ):
            raise ExecutionError(f"Dataset '{self.dataset_id}' already exists locally.")

        archive_raw_data_path = None
        archive_raw_labels_path = None
        if self.dataset.state == "DEVELOPMENT":
            archive_raw_data_path = os.path.join(
                root_archive_folder, archive_config["raw_data"]
            )
            archive_raw_labels_path = os.path.join(
                root_archive_folder, archive_config["raw_labels"]
            )
            if not os.path.exists(archive_raw_data_path) or not os.path.exists(
                archive_raw_labels_path
            ):
                raise ExecutionError("No raw data in archive")

        # TODO: Add more checks (later) comparing dataset generated_uid and so

        self.archive_prepared_dataset_path = archive_prepared_dataset_path
        self.archive_raw_data_path = archive_raw_data_path
        self.archive_raw_labels_path = archive_raw_labels_path

    def process_tarfiles(self):
        # Moves extarcted folders from medperf tmp path into the right destinations.
        # Moves raw data paths only if the dataset is in development.

        remove_path(self.dataset.path)
        move_folder(self.archive_prepared_dataset_path, self.dataset.path)
        self.dataset.set_raw_paths("", "")

        if self.dataset.state == "OPERATION":
            return

        # For development datasets, move raw data as well
        os.makedirs(self.raw_data_path, exist_ok=True)
        new_raw_data_path = os.path.join(
            self.raw_data_path, os.path.basename(self.archive_raw_data_path)
        )
        new_raw_labels_path = os.path.join(
            self.raw_data_path, os.path.basename(self.archive_raw_labels_path)
        )

        same_raw_data_and_labels = os.path.samefile(
            self.archive_raw_data_path, self.archive_raw_labels_path
        )
        move_folder(self.archive_raw_data_path, new_raw_data_path)
        if not same_raw_data_and_labels:
            move_folder(self.archive_raw_labels_path, new_raw_labels_path)

        self.dataset.set_raw_paths(new_raw_data_path, new_raw_labels_path)
