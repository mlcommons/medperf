from typing import List
import yaml
import os
import logging

from medperf.ui import UI
from medperf.config import config
from medperf.utils import get_dsets, approval_prompt, pretty_error


class Dataset:
    def __init__(self, data_uid: int, ui: UI):
        """Creates a new dataset instance

        Args:
            data_uid (int): The dataset UID as found inside ~/medperf/data/

        Raises:
            NameError: If the dataset with the given UID can't be found, this is thrown.
        """
        data_uid = self.__full_uid(data_uid, ui)
        self.generated_uid = data_uid
        self.dataset_path = os.path.join(config["data_storage"], str(data_uid))
        self.data_path = os.path.join(self.dataset_path, "data")
        self.registration = self.get_registration()
        self.uid = self.registration["uid"]
        self.name = self.registration["name"]
        self.description = self.registration["description"]
        self.location = self.registration["location"]
        self.preparation_cube_uid = self.registration["data_preparation_mlcube"]
        self.split_seed = self.registration["split_seed"]
        self.metadata = self.registration["metadata"]
        self.status = self.registration["status"]

    @classmethod
    def all(cls, ui: UI) -> List["Dataset"]:
        """Gets and creates instances of all the locally prepared datasets

        Returns:
            List[Dataset]: a list of Dataset instances.
        """
        logging.info("Retrieving all datasets")
        data_storage = config["data_storage"]
        try:
            uids = next(os.walk(data_storage))[1]
        except StopIteration:
            logging.warning("Couldn't iterate over the dataset directory")
            pretty_error("Couldn't iterate over the dataset directory")
        tmp_prefix = config["tmp_reg_prefix"]
        dsets = []
        for uid in uids:
            not_tmp = not uid.startswith(tmp_prefix)
            reg_path = os.path.join(data_storage, uid, config["reg_file"])
            registered = os.path.exists(os.path.join(reg_path))
            if not_tmp and registered:
                dsets.append(cls(uid, ui))
        return dsets

    def __full_uid(self, uid_hint: str, ui: UI) -> str:
        """Returns the found UID that starts with the provided UID hint

        Args:
            uid_hint (int): a small initial portion of an existing local dataset UID

        Raises:
            NameError: If no dataset is found starting with the given hint, this is thrown.
            NameError: If multiple datasets are found starting with the given hint, this is thrown.

        Returns:
            str: the complete UID
        """
        dsets = get_dsets()
        match = [uid for uid in dsets if uid.startswith(str(uid_hint))]
        if len(match) == 0:
            pretty_error(f"No dataset was found with uid hint {uid_hint}.", ui)
        elif len(match) > 1:
            pretty_error(f"Multiple datasets were found with uid hint {uid_hint}.", ui)
        else:
            return match[0]

    def get_registration(self) -> dict:
        """Retrieves the registration information.

        Returns:
            dict: registration information as key-value pairs.
        """
        regfile = os.path.join(self.dataset_path, config["reg_file"])
        with open(regfile, "r") as f:
            reg = yaml.full_load(f)
        return reg

    def request_association_approval(self, benchmark: "Benchmark", ui: UI) -> bool:
        """Prompts the user for aproval regarding the association of the dataset
        with a given benchmark.

        Args:
            benchmark (Benchmark): Benchmark to be associated with

        Returns:
            bool: Wether the user approved the association or not
        """
        if self.status == "APPROVED":
            return True

        approved = approval_prompt(
            f"Please confirm that you would like to associate the dataset '{self.name}' with the benchmark '{benchmark.name}' [Y/n]",
            ui,
        )
        return approved
