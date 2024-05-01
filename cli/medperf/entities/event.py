from datetime import datetime
import os
from typing import Optional
from medperf.entities.interface import Entity
import medperf.config as config
from medperf.entities.schemas import MedperfSchema
from medperf.account_management import get_medperf_user_data
import yaml


class TrainingEvent(Entity, MedperfSchema):
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

    training_exp: int
    participants: dict
    finished: bool = False
    finished_at: Optional[datetime]
    report: Optional[dict]

    @staticmethod
    def get_type():
        return "training event"

    @staticmethod
    def get_storage_path():
        return config.training_events_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_training_event

    @staticmethod
    def get_metadata_filename():
        return config.training_event_file

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_training_event

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.generated_uid = self.name
        self.participants_list_path = os.path.join(
            self.path, config.participants_list_filename
        )
        self.agg_out_logs = os.path.join(self.path, config.training_out_agg_logs)
        self.col_out_logs = os.path.join(self.path, config.training_out_col_logs)
        self.out_weights = os.path.join(self.path, config.training_out_weights)
        self.report_path = os.path.join(
            self.path, config.training_report_folder, config.training_report_file
        )

    @classmethod
    def from_experiment(cls, training_exp_uid: int) -> "TrainingEvent":
        meta = config.comms.get_experiment_event(training_exp_uid)
        ca = cls(**meta)
        ca.write()
        return ca

    @classmethod
    def _Entity__remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_training_events
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_training_events
        return comms_fn

    def prepare_participants_list(self):
        with open(self.participants_list_path, "w") as f:
            yaml.dump(self.participants, f)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Experiment": self.training_exp,
            "Generated Hash": self.generated_uid,
            "Participants": self.participants,
            "Created At": self.created_at,
            "Registered": self.is_registered,
            "Finished": self.finished,
            "Report": self.report,
        }
