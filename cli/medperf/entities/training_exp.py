import os
from medperf.commands.association.utils import get_experiment_associations
import yaml
from typing import List, Optional
from pydantic import HttpUrl, Field

import medperf.config as config
from medperf.entities.interface import Entity
from medperf.entities.schemas import MedperfSchema, ApprovableSchema, DeployableSchema
from medperf.account_management import get_medperf_user_data


class TrainingExp(Entity, MedperfSchema, ApprovableSchema, DeployableSchema):
    """
    Class representing a TrainingExp

    a training_exp is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A TrainingExp instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    description: Optional[str] = Field(None, max_length=256)
    docs_url: Optional[HttpUrl]
    demo_dataset_tarball_url: str
    demo_dataset_tarball_hash: Optional[str]
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    fl_mlcube: int
    fl_admin_mlcube: Optional[int]
    plan: dict = {}
    metadata: dict = {}
    user_metadata: dict = {}

    @staticmethod
    def get_type():
        return "training experiment"

    @staticmethod
    def get_storage_path():
        return config.training_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_training_exp

    @staticmethod
    def get_metadata_filename():
        return config.training_exps_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_training_exp

    def __init__(self, *args, **kwargs):
        """Creates a new training_exp instance

        Args:
            training_exp_desc (Union[dict, TrainingExpModel]): TrainingExp instance description
        """
        super().__init__(*args, **kwargs)

        self.plan_path = os.path.join(self.path, config.training_exp_plan_filename)
        self.status_path = os.path.join(self.path, config.training_exp_status_filename)

    @property
    def local_id(self):
        return self.name

    @classmethod
    def remote_prefilter(cls, filters: dict) -> callable:
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
    def get_datasets_uids(cls, training_exp_uid: int) -> List[int]:
        """Retrieves the list of models associated to the training_exp

        Args:
            training_exp_uid (int): UID of the training_exp.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[int]: List of mlcube uids
        """
        associations = get_experiment_associations(
            experiment_id=training_exp_uid,
            experiment_type="training_exp",
            component_type="dataset",
            approval_status="APPROVED",
        )
        datasets_uids = [assoc["dataset"] for assoc in associations]
        return datasets_uids

    @classmethod
    def get_datasets_with_users(cls, training_exp_uid: int) -> List[int]:
        """Retrieves the list of models associated to the training_exp

        Args:
            training_exp_uid (int): UID of the training_exp.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[int]: List of mlcube uids
        """
        uids_with_users = config.comms.get_training_datasets_with_users(
            training_exp_uid
        )
        return uids_with_users

    def prepare_plan(self):
        with open(self.plan_path, "w") as f:
            yaml.dump(self.plan, f)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            "FL Container": int(self.fl_mlcube),
            "Plan": self.plan,
            "State": self.state,
            "Registered": self.is_registered,
            "Approval Status": self.approval_status,
        }
