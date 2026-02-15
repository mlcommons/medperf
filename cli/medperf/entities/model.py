from typing import List, Optional

from pydantic import validator
import medperf.config as config
from medperf.entities.interface import Entity
from medperf.entities.schemas import DeployableSchema
from medperf.account_management import get_medperf_user_data
from medperf.commands.association.utils import get_user_associations


class Model(Entity, DeployableSchema):
    """
    Class representing a Model

    A model can be backed by either a container (MlCube) or a
    file-based asset, allowing models to be either containerized
    or simple file artifacts.
    """

    type: str  # ASSET or CONTAINER
    container: Optional[int]
    asset: Optional[int]
    metadata: dict = {}
    user_metadata: dict = {}

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

    @validator("container", pre=True, always=True)
    def check_container(cls, v, *, values, **kwargs):
        if v is not None and not isinstance(v, int) and not values["for_test"]:
            raise ValueError(
                "container must be an integer if not running a compatibility test"
            )
        return v

    @validator("asset", pre=True, always=True)
    def check_asset(cls, v, *, values, **kwargs):
        if v is not None and not isinstance(v, int) and not values["for_test"]:
            raise ValueError(
                "asset must be an integer if not running a compatibility test"
            )
        return v

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def local_id(self):
        return self.name

    @staticmethod
    def remote_prefilter(filters: dict) -> callable:
        comms_fn = config.comms.get_models
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_models
        return comms_fn

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
            "Container": self.container,
            "Asset": self.asset,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
