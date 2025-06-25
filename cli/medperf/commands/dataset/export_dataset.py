import os
from medperf.entities.dataset import Dataset
from medperf.utils import sanitize_path, tar, generate_tmp_path
import medperf.config as config
from medperf.exceptions import ExecutionError, MedperfException
import yaml


class ExportDataset:
    @classmethod
    def run(cls, dataset_id: str, output_path: str):
        export_dataset = cls(dataset_id, output_path)
        export_dataset.prepare()
        export_dataset.create_tar()

    def __init__(self, dataset_id: str, output_path: str):
        self.dataset_id = dataset_id
        output_path = os.path.join(output_path, str(dataset_id)) + ".gz"
        self.output_path = sanitize_path(output_path)
        self.dataset = Dataset.get(self.dataset_id)

        # this will contain what goes into the archive
        self.folders_paths = []

        # this will contain necessary information for untarring the archive later
        # It will contain the current used server, the dataset id, and
        # the raw data folder names within the archive if the dataset is in development
        self.archive_config = {}

    def _add_raw_paths(self):
        data_path, labels_path = self.dataset.get_raw_paths()

        # checks if raw_data_path exists
        if not os.path.exists(data_path):
            raise ExecutionError(f"Cannot find raw data path at '{data_path}'")
        if not os.path.exists(labels_path):
            raise ExecutionError(f"Cannot find raw labels path at '{labels_path}'")

        self.archive_config["raw_data"] = os.path.basename(data_path)
        self.archive_config["raw_labels"] = os.path.basename(labels_path)

        self.folders_paths.append(data_path)

        # Don't archive the same folder twice
        if not os.path.samefile(data_path, labels_path):
            self.folders_paths.append(labels_path)

    def prepare(self):
        self.folders_paths.append(self.dataset.path)

        # Gets server name to be added in paths.yaml. This will be checked during import
        # to make sure the same server is used
        self.archive_config = {"server": config.server, "dataset": self.dataset_id}

        # If the dataset is in development, it'll need the raw paths as well.
        if self.dataset.state == "DEVELOPMENT":
            self._add_raw_paths()

        tmp_path = generate_tmp_path()
        os.makedirs(tmp_path, exist_ok=True)
        archive_config_file = os.path.join(tmp_path, config.archive_config_filename)

        with open(archive_config_file, "w") as f:
            yaml.dump(self.archive_config, f)

        self.folders_paths.append(archive_config_file)

    def create_tar(self):
        # A sanity check for edge cases where raw paths have same basename
        # or have the same basename as the prepared data path
        basenames = [os.path.basename(path) for path in self.folders_paths]
        if len(basenames) != len(set(basenames)):
            raise MedperfException("Some folders to be archived have same basenames.")

        # create the archive
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        tar(self.output_path, self.folders_paths)
