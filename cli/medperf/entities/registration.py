import yaml
from datetime import datetime
from pathlib import Path
import os

from medperf.ui import UI
from medperf.utils import (
    approval_prompt,
    dict_pretty_print,
    get_folder_sha1,
    pretty_error,
)
from medperf.comms import Comms
from medperf.config import config
from medperf.entities import Cube, Dataset


class Registration:
    def __init__(
        self,
        cube: Cube,
        name: str = None,
        description: str = None,
        location: str = None,
    ):
        """Creates a registration instance

        Args:
            cube (Cube): Instance of the cube used for creating the registration.
            owner (str): UID of the user
            name (str, optional): Assigned name. Defaults to None.
            description (str, optional): Assigned description. Defaults to None.
            location (str, optional): Assigned location. Defaults to None.
        """
        self.cube = cube
        self.stats = self.__get_stats()
        dt = datetime.now()
        self.reg_time = int(datetime.timestamp(dt))
        self.name = name
        self.description = description
        self.location = location
        self.status = "PENDING"
        self.uid = None
        self.path = None

    def generate_uid(self, out_path: str) -> str:
        """Auto-generates an UID based on the contents of the registration

        Args:
            out_path (str): location of the prepared dataset
        Returns:
            str: generated UID
        """
        self.uid = get_folder_sha1(out_path)
        return self.uid

    def __get_stats(self) -> dict:
        """Unwinds the cube output statistics location and retrieves the statistics data

        Returns:
            dict: dataset statistics as key-value pairs.
        """
        stats_path = self.cube.get_default_output("statistics", "output_path")
        with open(stats_path, "r") as f:
            stats = yaml.full_load(f)

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
            "split_seed": 0,
            "data_preparation_mlcube": self.cube.uid,
            "generated_uid": self.uid,
            "metadata": self.stats,
            "status": self.status,
        }

        if self.uid is not None:
            registration.update({"uid": self.uid})

        return registration

    def retrieve_additional_data(self, ui: UI):
        """Prompts the user for the name, description and location
        """
        self.name = ui.prompt("Provide a dataset name: ")
        self.description = ui.prompt("Provide a description:  ")
        self.location = ui.prompt("Provide a location:     ")

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

    def to_permanent_path(self, out_path: str, uid: int) -> str:
        """Renames the temporary data folder to permanent one using the hash of
        the registration file

        Args:
            out_path (str): current temporary location of the data
            uid (int): UID of registered dataset. Obtained after uploading to comms

        Returns:
            str: renamed location of the data.
        """
        new_path = os.path.join(str(Path(out_path).parent), str(uid))
        os.rename(out_path, new_path)
        self.path = new_path
        return new_path

    def write(self, out_path: str, filename: str = config["reg_file"]) -> str:
        """Writes the registration into disk

        Args:
            out_path (str): path where the file will be created
            filename (str, optional): name of the file. Defaults to config["reg_file"].

        Returns:
            str: path to the created registration file
        """
        data = self.todict()
        filepath = os.path.join(out_path, filename)
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
        if self.uid is None:
            pretty_error(
                "The registration doesn't have an uid yet. Generate it before running this method.",
                ui,
                add_instructions=False,
            )

        dsets = Dataset.all(ui)
        registered_uids = [dset.registration["generated_uid"] for dset in dsets]
        return self.uid in registered_uids
