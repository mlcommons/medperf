from typing import List
import yaml
import os
import logging

from medperf.config import config
from medperf.utils import get_file_sha1, get_dsets, approval_prompt


class Dataset:
    def __init__(self, data_uid: int):
        """Creates a new dataset instance

        Args:
            data_uid (int): The dataset UID as found inside ~/medperf/data/

        Raises:
            NameError: If the dataset with the given UID can't be found, this is thrown.
        """
        data_uid = self.__full_uid(data_uid)
        self.data_uid = data_uid
        self.dataset_path = os.path.join(config["data_storage"], str(data_uid))
        if not os.path.exists(self.dataset_path):
            raise NameError("the dataset with provided UID couldn't be found")
        self.data_path = os.path.join(self.dataset_path, "data")
        self.registration = self.get_registration()
        self.name = self.registration["name"]
        self.description = self.registration["description"]
        self.location = self.registration["location"]
        self.preparation_cube_uid = self.registration["data_preparation_mlcube"]
        self.split_seed = self.registration["split_seed"]
        self.metadata = self.registration["metadata"]
        self.generated_uid = self.registration["generated_uid"]
        self.status = self.registration["status"]

    @classmethod
    def all(cls) -> List["Dataset"]:
        """Gets and creates instances of all the locally prepared datasets

        Returns:
            List[Dataset]: a list of Dataset instances.
        """
        logging.info("Retrieving all datasets")
        try:
            uids = next(os.walk(config["data_storage"]))[1]
        except StopIteration:
            logging.warning("Couldn't iterate over the dataset directory")
            exit()
        tmp_prefix = config["tmp_reg_prefix"]
        dsets = [cls(uid) for uid in uids if not uid.startswith(tmp_prefix)]
        return dsets

    def is_valid(self) -> bool:
        """Checks the validity of the dataset instances by comparing it to its hash

        Returns:
            bool: Wether the dataset matches the expected hash
        """
        regfile_path = os.path.join(self.dataset_path, "registration-info.yaml")
        return get_file_sha1(regfile_path) == self.data_uid

    def __full_uid(self, uid_hint: str) -> str:
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
            raise NameError("No dataset was found with provided uid hint.")
        if len(match) > 1:
            raise NameError("Multiple datasets were found with provided uid hint.")
        return match[0]

    def get_registration(self) -> dict:
        """Retrieves the registration information.

        Returns:
            dict: registration information as key-value pairs.
        """
        regfile = os.path.join(self.dataset_path, "registration-info.yaml")
        with open(regfile, "r") as f:
            reg = yaml.full_load(f)
        return reg

    def request_association_approval(self, benchmark: "Benchmark") -> bool:
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
            f"Please confirm that you would like to associate the dataset '{self.name}' with the benchmark '{benchmark.name}' [Y/n]"
        )
        return approved
