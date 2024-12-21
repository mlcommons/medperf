import os
from medperf.entities.dataset import Dataset
from medperf.utils import tar
import medperf.config as config
from medperf.exceptions import ExecutionError
import yaml


class ExportDataset:
    @classmethod
    def run(cls, dataset_id: str, output_path: str):
        export_dataset = cls(dataset_id, output_path)
        export_dataset.prepare()
        export_dataset.create_tar()

    def __init__(self, dataset_id: str, output_path: str):
        self.dataset_id = dataset_id
        self.output_path = os.path.join(output_path, dataset_id) + ".gz"
        self.folders_paths = []
        self.dataset = Dataset.get(self.dataset_id)
        self.dataset_storage = self.dataset.get_storage_path()
        self.dataset_tar_folder = (
            config.dataset_backup_foldername + self.dataset_id
        )  # name of the folder that will contain the backup

    def _prepare_development_dataset(self):
        raw_data_paths = self.dataset.get_raw_paths()

        for folder in raw_data_paths:
            # checks if raw_data_path exists and not empty
            if not (os.path.exists(folder) and os.listdir(folder)):
                raise ExecutionError(f"Cannot find raw data paths at '{folder}'")
            self.folders_paths.append(folder)

        data_path, labels_path = raw_data_paths
        self.paths["data"] = os.path.basename(data_path)
        self.paths["labels"] = os.path.basename(labels_path)

    def prepare(self):
        # Gets server name to be added in paths.yaml for comparing between local and remote servers
        # which will save folders names (what each one points to.
        dataset_path = os.path.join(self.dataset_storage, self.dataset_id)
        self.folders_paths.append(dataset_path)
        self.paths = {"server": config.server, "dataset": self.dataset_id}

        # If the dataset is in development, it'll need the raw paths as well.
        if self.dataset.state == "DEVELOPMENT":
            self._prepare_development_dataset()

        paths_path = os.path.join(config.tmp_folder, config.backup_config_filename)

        # paths.yaml will be created in medperf tmp directory
        with open(paths_path, "w") as f:
            yaml.dump(self.paths, f)

        self.folders_paths.append(paths_path)
        config.tmp_paths.append(paths_path)

    def create_tar(self):
        tar(self.output_path, self.folders_paths, self.dataset_tar_folder)
