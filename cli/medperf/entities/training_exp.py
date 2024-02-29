import os
from medperf.exceptions import MedperfException
import yaml
import logging
from typing import List, Optional, Union
from pydantic import HttpUrl, Field, validator

import medperf.config as config
from medperf.entities.interface import Entity, Uploadable
from medperf.utils import get_dataset_common_name
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError
from medperf.entities.schemas import MedperfSchema, ApprovableSchema, DeployableSchema
from medperf.account_management import get_medperf_user_data, read_user_account


class TrainingExp(
    Entity, Uploadable, MedperfSchema, ApprovableSchema, DeployableSchema
):
    """
    Class representing a TrainingExp

    a training_exp is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A TrainingExp instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    description: Optional[str] = Field(None, max_length=20)
    docs_url: Optional[HttpUrl]
    demo_dataset_tarball_url: Optional[str]
    demo_dataset_tarball_hash: Optional[str]
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    fl_mlcube: int
    public_key: Optional[str]
    datasets: List[int] = None
    metadata: dict = {}
    user_metadata: dict = {}
    state: str = "DEVELOPMENT"

    @validator("datasets", pre=True, always=True)
    def set_default_datasets_value(cls, value, values, **kwargs):
        if not value:
            # Empty or None value assigned
            return []
        return value

    def __init__(self, *args, **kwargs):
        """Creates a new training_exp instance

        Args:
            training_exp_desc (Union[dict, TrainingExpModel]): TrainingExp instance description
        """
        super().__init__(*args, **kwargs)

        self.generated_uid = self.name
        path = config.training_folder
        if self.id:
            path = os.path.join(path, str(self.id))
        else:
            path = os.path.join(path, self.generated_uid)
        self.path = path
        self.cert_path = os.path.join(path, config.ca_cert_folder)
        self.cols_path = os.path.join(path, config.training_exp_cols_filename)

    @classmethod
    def all(cls, local_only: bool = False, filters: dict = {}) -> List["TrainingExp"]:
        """Gets and creates instances of all retrievable training_exps

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.

        Returns:
            List[TrainingExp]: a list of TrainingExp instances.
        """
        logging.info("Retrieving all training_exps")
        training_exps = []

        if not local_only:
            training_exps = cls.__remote_all(filters=filters)

        remote_uids = set([training_exp.id for training_exp in training_exps])

        local_training_exps = cls.__local_all()

        training_exps += [
            training_exp
            for training_exp in local_training_exps
            if training_exp.id not in remote_uids
        ]

        return training_exps

    @classmethod
    def __remote_all(cls, filters: dict) -> List["TrainingExp"]:
        training_exps = []
        try:
            comms_fn = cls.__remote_prefilter(filters)
            training_exps_meta = comms_fn()
            for training_exp_meta in training_exps_meta:
                # Loading all related models for all training_exps could be expensive.
                # Most probably not necessary when getting all training_exps.
                # If associated models for a training_exp are needed then use TrainingExp.get()
                training_exp_meta["datasets"] = []
            training_exps = [cls(**meta) for meta in training_exps_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all training_exps from the server"
            logging.warning(msg)

        return training_exps

    @classmethod
    def __remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_training_exps
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_training_exps
        return comms_fn

    @classmethod
    def __local_all(cls) -> List["TrainingExp"]:
        training_exps = []
        training_exps_storage = config.training_folder
        try:
            uids = next(os.walk(training_exps_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over training_exps directory"
            logging.warning(msg)
            raise MedperfException(msg)

        for uid in uids:
            meta = cls.__get_local_dict(uid)
            training_exp = cls(**meta)
            training_exps.append(training_exp)

        return training_exps

    @classmethod
    def get(
        cls, training_exp_uid: Union[str, int], local_only: bool = False
    ) -> "TrainingExp":
        """Retrieves and creates a TrainingExp instance from the server.
        If training_exp already exists in the platform then retrieve that
        version.

        Args:
            training_exp_uid (str): UID of the training_exp.
            comms (Comms): Instance of a communication interface.

        Returns:
            TrainingExp: a TrainingExp instance with the retrieved data.
        """

        if not str(training_exp_uid).isdigit() or local_only:
            return cls.__local_get(training_exp_uid)

        try:
            return cls.__remote_get(training_exp_uid)
        except CommunicationRetrievalError:
            logging.warning(f"Getting TrainingExp {training_exp_uid} from comms failed")
            logging.info(f"Looking for training_exp {training_exp_uid} locally")
            return cls.__local_get(training_exp_uid)

    @classmethod
    def __remote_get(cls, training_exp_uid: int) -> "TrainingExp":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            dset_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving training_exp {training_exp_uid} remotely")
        training_exp_dict = config.comms.get_training_exp(training_exp_uid)
        datasets = cls.get_datasets_uids(training_exp_uid)
        training_exp_dict["datasets"] = datasets
        training_exp = cls(**training_exp_dict)
        training_exp.write()
        return training_exp

    @classmethod
    def __local_get(cls, training_exp_uid: Union[str, int]) -> "TrainingExp":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            dset_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving training_exp {training_exp_uid} locally")
        training_exp_dict = cls.__get_local_dict(training_exp_uid)
        training_exp = cls(**training_exp_dict)
        return training_exp

    @classmethod
    def __get_local_dict(cls, training_exp_uid) -> dict:
        """Retrieves a local training_exp information

        Args:
            training_exp_uid (str): uid of the local training_exp

        Returns:
            dict: information of the training_exp
        """
        logging.info(f"Retrieving training_exp {training_exp_uid} from local storage")
        training_exp_storage = os.path.join(config.training_folder, str(training_exp_uid))
        training_exp_file = os.path.join(
            training_exp_storage, config.training_exps_filename
        )
        if not os.path.exists(training_exp_file):
            raise InvalidArgumentError(
                "No training_exp with the given uid could be found"
            )
        with open(training_exp_file, "r") as f:
            data = yaml.safe_load(f)

        return data

    @classmethod
    def get_datasets_uids(cls, training_exp_uid: int) -> List[int]:
        """Retrieves the list of models associated to the training_exp

        Args:
            training_exp_uid (int): UID of the training_exp.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[int]: List of mlcube uids
        """
        return config.comms.get_experiment_datasets(training_exp_uid)

    def todict(self) -> dict:
        """Dictionary representation of the training_exp instance

        Returns:
        dict: Dictionary containing training_exp information
        """
        return self.extended_dict()

    def write(self) -> str:
        """Writes the training_exp into disk

        Args:
            filename (str, optional): name of the file. Defaults to config.training_exps_filename.

        Returns:
            str: path to the created training_exp file
        """
        data = self.todict()
        training_exp_file = os.path.join(self.path, config.training_exps_filename)
        if not os.path.exists(training_exp_file):
            os.makedirs(self.path, exist_ok=True)
        with open(training_exp_file, "w") as f:
            yaml.dump(data, f)

        # write cert
        os.makedirs(self.cert_path, exist_ok=True)
        cert_file = os.path.join(self.cert_path, "cert.crt")
        with open(cert_file, "w") as f:
            f.write(self.public_key)

        # write cols
        dataset_owners_emails = [""] * len(
            self.datasets
        )  # TODO (this will need some work)
        # our medperf's user info endpoint is not public
        # emails currently are not stored in medperf (auth0 only. in access tokens as well)
        cols = [
            get_dataset_common_name(email, dataset_id, self.id)
            for email, dataset_id in zip(dataset_owners_emails, self.datasets)
        ]
        with open(self.cols_path, "w") as f:
            f.write("\n".join(cols))

        return training_exp_file

    def upload(self):
        """Uploads a training_exp to the server

        Args:
            comms (Comms): communications entity to submit through
        """
        if self.for_test:
            raise InvalidArgumentError("Cannot upload test training_exps.")
        body = self.todict()
        updated_body = config.comms.upload_training_exp(body)
        updated_body["datasets"] = body["datasets"]
        return updated_body

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            "FL MLCube": int(self.fl_mlcube),
            "Associated Datasets": ",".join(map(str, self.datasets)),
            "State": self.state,
            "Registered": self.is_registered,
            "Approval Status": self.approval_status,
        }
