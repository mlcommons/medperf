from typing import List, Optional

from medperf.exceptions import MedperfException
import medperf.config as config
from medperf.entities.interface import Entity
from medperf.entities.schemas import ModelSchema
from medperf.entities.cube import Cube
from medperf.entities.asset import Asset
from medperf.account_management import get_medperf_user_data
from medperf.commands.association.utils import get_user_associations
from medperf.entities.utils import handle_validation_error


class Model(Entity):
    """
    Class representing a Model

    A model can be backed by either a container (MlCube) or a
    file-based asset, allowing models to be either containerized
    or simple file artifacts.
    """

    @staticmethod
    def get_type():
        return "model"

    @staticmethod
    def get_storage_path():
        return config.models_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_model

    @staticmethod
    def get_metadata_filename():
        return config.model_metadata_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_model

    @handle_validation_error
    def __init__(self, **kwargs):
        self._model = ModelSchema(**kwargs)
        super().__init__()
        self.state = self._model.state
        self.type = self._model.type
        self.container = self._model.container
        self.asset = self._model.asset
        self.metadata = self._model.metadata
        self.user_metadata = self._model.user_metadata

    @property
    def local_id(self):
        return self.name

    def is_asset(self):
        return self.type == "ASSET"

    def is_container(self):
        return self.type == "CONTAINER"

    @property
    def container_obj(self):
        if not self.is_container():
            raise MedperfException("Model is not a container")
        return Cube(**self.container.dict())

    @property
    def asset_obj(self):
        if not self.is_asset():
            raise MedperfException("Model is not an asset")
        return Asset(**self.asset.dict())

    def is_encrypted(self) -> bool:
        return self.is_container() and self.container_obj.is_encrypted()

    def requires_cc(self):
        # for now, let's do this
        return self.is_asset() and self.asset_obj.is_local()

    def get_cc_config(self):
        cc_values = self.user_metadata.get("cc", {})
        return cc_values.get("config", {})

    def set_cc_config(self, cc_config: dict):
        if "cc" not in self.user_metadata:
            self.user_metadata["cc"] = {}
        self.user_metadata["cc"]["config"] = cc_config

    def get_cc_policy(self):
        cc_values = self.user_metadata.get("cc", {})
        return cc_values.get("policy", {})

    def set_cc_policy(self, cc_policy: dict):
        if "cc" not in self.user_metadata:
            self.user_metadata["cc"] = {}
        self.user_metadata["cc"]["policy"] = cc_policy

    def is_cc_configured(self):
        return self.get_cc_config() != {}

    @staticmethod
    def remote_prefilter(filters: dict) -> callable:
        comms_fn = config.comms.get_models
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_models
        return comms_fn

    @classmethod
    def get_by_container(cls, container_id: int) -> Optional["Model"]:
        """Returns the Model that wraps the given container, or None if not found.

        Args:
            container_id (int): The container (Cube) ID to look up.

        Returns:
            Model or None
        """
        model_metadata = config.comms.get_container_model(container_id)
        return cls(**model_metadata)

    @classmethod
    def get_by_asset(cls, asset_id: int) -> Optional["Model"]:
        """Returns the Model that wraps the given asset, or None if not found.

        Args:
            asset_id (int): The asset ID to look up.

        Returns:
            Model or None
        """
        model_metadata = config.comms.get_asset_model(asset_id)
        return cls(**model_metadata)

    @classmethod
    def get_benchmarks_associations(cls, model_uid: int) -> List[dict]:
        experiment_type = "benchmark"
        component_type = "model"

        associations = get_user_associations(
            experiment_type=experiment_type,
            component_type=component_type,
            approval_status=None,
        )

        associations = [a for a in associations if a["model"] == model_uid]

        return associations

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Type": self.type,
            "State": self.state,
            "Container": self.container.id if self.is_container() else None,
            "Asset": self.asset.id if self.is_asset() else None,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
