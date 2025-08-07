from __future__ import annotations
from medperf.entities.interface import Entity
from medperf.account_management import get_medperf_user_data
from medperf.utils import get_pki_assets_path
from medperf import config
from typing import Optional
from medperf.entities.ca import CA


class Certificate(Entity):
    """
    Class representing a Certificate uploaded to the MedPerf server
    Currently only supports Client Certificates (ie common name is a email)
    """

    certificate_content: bytes
    ca_id: int
    ca_name: Optional[str]

    @staticmethod
    def get_type():
        return "certificate"

    @staticmethod
    def get_storage_path():
        return config.pki_assets

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_certificate

    @staticmethod
    def get_metadata_filename():
        return config.certificate_metadata_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_certificate

    @property
    def local_id(self):
        return config.certificate_file

    @property
    def user_email(self) -> str:
        return get_medperf_user_data()["email"]

    @property
    def path(self) -> str:
        if self.ca_name is None:
            ca = CA.get(self.ca_id)
            self.ca_name = ca.name
        return get_pki_assets_path(common_name=self.user_email, ca_name=self.ca_name)

    @classmethod
    def get_list_from_benchmark_model_ca(
        cls, benchmark_id: int, model_id: int, ca_id: int
    ) -> list[Certificate]:
        cert_data_list = config.comms.get_certificates_from_benchmark_model_ca(
            benchmark_id=benchmark_id, model_id=model_id, ca_id=ca_id
        )

        cert_obj_list = [cls(**cert_data) for cert_data in cert_data_list]
        return cert_obj_list

    @classmethod
    def remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_certificates
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_certificates
        return comms_fn

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "CA ID": self.ca_id,
            "State": self.state,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
