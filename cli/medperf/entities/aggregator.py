import os

from medperf.entities.interface import Entity
from medperf.entities.schemas import AggregatorSchema

import medperf.config as config
from medperf.account_management import get_medperf_user_data
import yaml
from medperf.entities.utils import handle_validation_error


class Aggregator(Entity):
    """
    Class representing a compatibility test report entry

    A test report is comprised of the components of a test execution:
    - data used, which can be:
        - a demo aggregator url and its hash, or
        - a raw data path and its labels path, or
        - a prepared aggregator uid
    - Data preparation cube if the data used was not already prepared
    - model cube
    - evaluator cube
    - results
    """

    @staticmethod
    def get_type():
        return "aggregator"

    @staticmethod
    def get_storage_path():
        return config.aggregators_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_aggregator

    @staticmethod
    def get_metadata_filename():
        return config.agg_file

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_aggregator

    @handle_validation_error
    def __init__(self, **kwargs):
        self._model = AggregatorSchema(**kwargs)
        super().__init__()
        self.metadata = self._model.metadata
        self.config = self._model.config
        self.aggregation_mlcube = self._model.aggregation_mlcube
        self._set_helper_attributes()

    def _set_helper_attributes(self):
        self.address = self.config["address"]
        self.port = self.config["port"]

        self.config_path = os.path.join(self.path, config.agg_config_file)

    @property
    def local_id(self):
        return self.name

    @classmethod
    def from_experiment(cls, training_exp_uid: int) -> "Aggregator":
        meta = config.comms.get_experiment_aggregator(training_exp_uid)
        agg = cls(**meta)
        agg.write()
        return agg

    @classmethod
    def remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_aggregators
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_aggregators
        return comms_fn

    def prepare_config(self):
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Address": self.address,
            "Container": int(self.aggregation_mlcube),
            "Port": self.port,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
