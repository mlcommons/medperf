import json
import os
from medperf.entities.interface import Entity
from medperf.entities.schemas import MedperfSchema
from pydantic import validator
import medperf.config as config
from medperf.account_management import get_medperf_user_data


class CA(Entity, MedperfSchema):
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

    metadata: dict = {}
    client_mlcube: int
    server_mlcube: int
    ca_mlcube: int
    config: dict

    @staticmethod
    def get_type():
        return "ca"

    @staticmethod
    def get_storage_path():
        return config.cas_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_ca

    @staticmethod
    def get_metadata_filename():
        return config.ca_file

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_ca

    @validator("config", pre=True, always=True)
    def check_config(cls, v, *, values, **kwargs):
        keys = set(v.keys())
        allowed_keys = {
            "address",
            "port",
            "fingerprint",
            "client_provisioner",
            "server_provisioner",
        }
        if keys != allowed_keys:
            raise ValueError(
                "CA config must contain these exact 5 keys:\n"
                "address, port, fingerprint, client_provisioner, server_provisioner"
            )
        return v

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.address = self.config["address"]
        self.port = self.config["port"]
        self.fingerprint = self.config["fingerprint"]
        self.client_provisioner = self.config["client_provisioner"]
        self.server_provisioner = self.config["server_provisioner"]

        self.config_path = os.path.join(self.path, config.ca_config_file)
        self.pki_assets = os.path.join(self.path, config.ca_cert_folder)

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
        comms_fn = config.comms.get_cas
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_cas
        return comms_fn

    def prepare_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Address": self.address,
            "fingerprint": self.fingerprint,
            "Port": self.port,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
