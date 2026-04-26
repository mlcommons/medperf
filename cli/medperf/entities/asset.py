import os

import yaml

from medperf.comms.entity_resources import resources
from medperf.utils import get_file_hash, remove_path, untar
from medperf.exceptions import InvalidEntityError, MedperfException
import medperf.config as config
from medperf.entities.interface import Entity
from medperf.entities.schemas import AssetSchema
from medperf.account_management import get_medperf_user_data
from medperf.entities.utils import handle_validation_error


class Asset(Entity):
    """
    Class representing an Asset

    An asset is a file-based artifact that can be used as a model
    component in the MedPerf platform.
    """

    @staticmethod
    def get_type():
        return "asset"

    @staticmethod
    def get_storage_path():
        return config.assets_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_asset

    @staticmethod
    def get_metadata_filename():
        return config.asset_metadata_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_asset

    @handle_validation_error
    def __init__(self, **kwargs):
        self._model = AssetSchema(**kwargs)
        super().__init__()
        self.state = self._model.state
        self.asset_hash = self._model.asset_hash
        self.asset_url = self._model.asset_url
        self.metadata = self._model.metadata
        self.user_metadata = self._model.user_metadata
        self._set_helper_attributes()

    def _set_helper_attributes(self):
        self.asset_files_path = os.path.join(self.path, config.asset_files_folder)

    @property
    def local_id(self):
        return self.name

    def is_local(self) -> bool:
        return self.asset_url == "local"

    def is_model(self) -> bool:
        return True

    def check_hash(self) -> bool:
        try:
            self.get_archive_path()
        except InvalidEntityError:
            return False
        return True

    @staticmethod
    def remote_prefilter(filters: dict) -> callable:
        comms_fn = config.comms.get_assets
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_assets
        return comms_fn

    def set_archive_path(self, source_path):
        asset_path_file = os.path.join(self.path, config.asset_local_archive_info_file)
        data = {"path": source_path}
        with open(asset_path_file, "w") as f:
            yaml.dump(data, f)

    def __get_local_archive_path(self):
        if self.asset_url != "local":
            raise MedperfException("Asset does not have a local archive path")

        asset_path_file = os.path.join(self.path, config.asset_local_archive_info_file)
        with open(asset_path_file) as f:
            data = yaml.safe_load(f)
        return data["path"]

    def __prepare_local_asset(self):
        asset_archive_path = self.__get_local_archive_path()
        if not os.path.exists(asset_archive_path):
            raise MedperfException("Local asset archive path does not exist")
        expected_hash = get_file_hash(asset_archive_path)
        if self.asset_hash != expected_hash:
            raise InvalidEntityError("Asset hash does not match the expected hash. ")
        return asset_archive_path

    def __download_remote_asset(self):
        asset_archive_path, self.asset_hash = resources.get_hashed_file(
            self.asset_url, self.asset_hash
        )
        return asset_archive_path

    def get_archive_path(self):
        if self.asset_url == "local":
            return self.__prepare_local_asset()
        else:
            return self.__download_remote_asset()

    def __extract_asset(self, archive_path):
        remove_path(self.asset_files_path)
        untar(archive_path, remove=False, extract_to=self.asset_files_path)

    def prepare_asset_files(self):
        archive_file_path = self.get_archive_path()
        self.__extract_asset(archive_file_path)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "State": self.state,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
