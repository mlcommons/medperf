import os
import yaml
from pathlib import Path

from medperf.utils import (
    get_folder_sha1,
    pretty_error,
    approval_prompt,
    dict_pretty_print,
)
from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset


class Registration:
    """
    Class representing a Dataset Registration

    A Registration object represents a prepared dataset that hasn't
    yet been registered on the platform. It contains the procedures
    required to successfully submit a dataset entry.
    """

    def __init__(
        self,
        cube: Cube,
        name: str = None,
        description: str = None,
        location: str = None,
        separate_labels: bool = False,
    ):
        """Creates a registration instance

        Args:
            cube (Cube): Instance of the cube used for creating the registration.
            owner (str): UID of the user
            name (str, optional): Assigned name. Defaults to None.
            description (str, optional): Assigned description. Defaults to None.
            location (str, optional): Assigned location. Defaults to None.
            separate_labels (bool, optional): Whether the labels should be separated from the data. Defaults to False.
        """
        self.cube = cube
        self.stats = self.__get_stats()
        self.name = name
        self.description = description
        self.split_seed = 0
        self.location = location
        self.status = "PENDING"
        self.generated_uid = None
        self.uid = None
        self.in_uid = None
        self.path = None
        self.separate_labels = separate_labels

    def generate_uids(self, in_path: str, out_path: str) -> str:
        """Auto-generates dataset UIDs for both input and output paths

        Args:
            in_path (str): location of the raw dataset
            out_path (str): location of the prepared dataset
        Returns:
            str: generated UID
        """
        self.in_uid = get_folder_sha1(in_path)
        self.generated_uid = get_folder_sha1(out_path)
        return self.generated_uid

    def __get_stats(self) -> dict:
        """Unwinds the cube output statistics location and retrieves the statistics data

        Returns:
            dict: dataset statistics as key-value pairs.
        """
        stats_path = self.cube.get_default_output("statistics", "output_path")
        with open(stats_path, "r") as f:
            stats = yaml.safe_load(f)

        return stats

    def todict(self) -> dict:
        """Dictionary representation of the registration

        Returns:
            dict: dictionary containing information pertaining the registration.
        """
        registration = {
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "split_seed": self.split_seed,
            "data_preparation_mlcube": self.cube.uid,
            "generated_uid": self.generated_uid,
            "input_data_hash": self.in_uid,
            "generated_metadata": self.stats,
            "status": self.status,
            "uid": self.uid,
            "state": "OPERATION",
            "separate_labels": self.separate_labels,
        }

        return registration

    def request_approval(self, ui: UI) -> bool:
        """Prompts the user for approval concerning uploading the registration to the comms.

        Returns:
            bool: Wether the user gave consent or not.
        """
        if self.status == "APPROVED":
            return True

        dict_pretty_print(self.todict(), ui)
        ui.print(
            "Above is the information and statistics that will be registered to the database"
        )
        approved = approval_prompt(
            "Do you approve the registration of the presented data to the MLCommons comms? [Y/n] ",
            ui,
        )
        return approved

    def to_permanent_path(self, out_path: str) -> str:
        """Renames the temporary data folder to permanent one using the hash of
        the registration file

        Args:
            out_path (str): current temporary location of the data

        Returns:
            str: renamed location of the data.
        """
        uid = self.generated_uid
        new_path = os.path.join(str(Path(out_path).parent), str(uid))
        if not os.path.exists(new_path):
            os.rename(out_path, new_path)
        self.path = new_path
        return new_path

    def write(self, filename: str = config.reg_file) -> str:
        """Writes the registration into disk

        Args:
            out_path (str): path where the file will be created
            filename (str, optional): name of the file. Defaults to config.reg_file.

        Returns:
            str: path to the created registration file
        """
        data = self.todict()
        filepath = os.path.join(self.path, filename)
        with open(filepath, "w") as f:
            yaml.dump(data, f)

        self.path = filepath
        return filepath

    def upload(self, comms: Comms) -> int:
        """Uploads the registration information to the comms.

        Args:
            comms (Comms): Instance of the comms interface.

        Returns:
            int: UID of registered dataset
        """
        dataset_uid = comms.upload_dataset(self.todict())
        return dataset_uid

    def is_registered(self, ui: UI) -> bool:
        """Checks if the entry has already been registered as a dataset. Uses the
        generated UID for comparison.

        Returns:
            bool: Wether the generated UID is already present in the registered datasets.
        """
        if self.generated_uid is None:
            pretty_error(
                "The registration doesn't have an uid yet. Generate it before running this method.",
                ui,
                add_instructions=False,
            )

        dsets = Dataset.all(ui)
        registered_uids = [dset.registration["generated_uid"] for dset in dsets]
        return self.generated_uid in registered_uids
