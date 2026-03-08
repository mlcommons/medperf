import os
from medperf.commands.association.utils import get_experiment_associations
import yaml
from typing import List
import medperf.config as config
from medperf.entities.interface import Entity
from medperf.entities.schemas import TrainingExpSchema
from medperf.account_management import get_medperf_user_data
from medperf.entities.utils import handle_validation_error


class TrainingExp(Entity):
    """
    Class representing a TrainingExp

    a training_exp is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A TrainingExp instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

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

    @handle_validation_error
    def __init__(self, **kwargs):
        """Creates a new training_exp instance

        Args:
            training_exp_desc (Union[dict, TrainingExpModel]): TrainingExp instance description
        """
        self._model = TrainingExpSchema(**kwargs)
        super().__init__()

        self.approved_at = self._model.approved_at
        self.approval_status = self._model.approval_status
        self.state = self._model.state
        self.description = self._model.description
        self.docs_url = self._model.docs_url
        self.demo_dataset_tarball_url = self._model.demo_dataset_tarball_url
        self.demo_dataset_tarball_hash = self._model.demo_dataset_tarball_hash
        self.demo_dataset_generated_uid = self._model.demo_dataset_generated_uid
        self.data_preparation_mlcube = self._model.data_preparation_mlcube
        self.fl_mlcube = self._model.fl_mlcube
        self.fl_admin_mlcube = self._model.fl_admin_mlcube
        self.plan = self._model.plan
        self.metadata = self._model.metadata
        self.user_metadata = self._model.user_metadata

        self._set_helper_attributes()

    def _set_helper_attributes(self):
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
