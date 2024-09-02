from medperf.entities.dataset import Dataset
from medperf import settings
from medperf.config_management import config
from medperf.utils import approval_prompt, dict_pretty_print, get_folders_hash
from medperf.exceptions import CleanExit, InvalidArgumentError
import yaml


class DatasetSetOperational:
    # TODO: this will be refactored when merging entity edit PR
    @classmethod
    def run(cls, dataset_id: int, approved: bool = False):
        preparation = cls(dataset_id, approved)
        preparation.validate()
        preparation.generate_uids()
        preparation.set_statistics()
        preparation.set_operational()
        preparation.update()
        preparation.write()

        return preparation.dataset.id

    def __init__(self, dataset_id: int, approved: bool):
        self.ui = config.ui
        self.dataset = Dataset.get(dataset_id)
        self.approved = approved

    def validate(self):
        if self.dataset.state == "OPERATION":
            raise InvalidArgumentError("The dataset is already operational")
        if not self.dataset.is_ready():
            raise InvalidArgumentError("The dataset is not checked")

    def generate_uids(self):
        """Auto-generates dataset UIDs for both input and output paths"""
        raw_data_path, raw_labels_path = self.dataset.get_raw_paths()
        prepared_data_path = self.dataset.data_path
        prepared_labels_path = self.dataset.labels_path

        in_uid = get_folders_hash([raw_data_path, raw_labels_path])
        generated_uid = get_folders_hash([prepared_data_path, prepared_labels_path])
        self.dataset.input_data_hash = in_uid
        self.dataset.generated_uid = generated_uid

    def set_statistics(self):
        with open(self.dataset.statistics_path, "r") as f:
            stats = yaml.safe_load(f)
        self.dataset.generated_metadata = stats

    def set_operational(self):
        self.dataset.state = "OPERATION"

    def update(self):
        body = self.todict()
        dict_pretty_print(body)
        msg = "Do you approve sending the presented data to MedPerf? [Y/n] "
        self.approved = self.approved or approval_prompt(msg)

        if self.approved:
            settings.comms.update_dataset(self.dataset.id, body)
            return

        raise CleanExit("Setting Dataset as operational was cancelled")

    def todict(self) -> dict:
        """Dictionary representation of the update body

        Returns:
            dict: dictionary containing information pertaining the dataset.
        """
        return {
            "input_data_hash": self.dataset.input_data_hash,
            "generated_uid": self.dataset.generated_uid,
            "generated_metadata": self.dataset.generated_metadata,
            "state": self.dataset.state,
        }

    def write(self) -> str:
        """Writes the registration into disk
        Args:
            filename (str, optional): name of the file. Defaults to config.reg_file.
        """
        self.dataset.write()
