from __future__ import annotations
import os
from medperf.entities.interface import Entity
from medperf.account_management import get_medperf_user_data
from medperf import config
from medperf.exceptions import MedperfException
from medperf.utils import generate_tmp_path
from pydantic import validator
import base64
from typing import List, Tuple


class Certificate(Entity):
    """
    Class representing a Certificate uploaded to the MedPerf server
    Currently only supports Client Certificates (ie common name is a email)
    """

    certificate_content_base64: str
    ca: int

    @validator("owner", pre=True, always=True)
    def check_required_owner(cls, v, *, values, **kwargs):
        if v is None:
            raise ValueError(
                "Internal error: The owner field is required for Certificate Entities "
            )
        return v

    @staticmethod
    def get_type():
        return "certificate"

    @staticmethod
    def get_storage_path():
        return config.certificates_folder

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
        return self.name

    def prepare_certificate_file(self):
        cert_folder = generate_tmp_path()
        os.makedirs(cert_folder, exist_ok=True)
        cert_file = os.path.join(cert_folder, config.certificate_file)
        certificate_content_bytes = base64.b64decode(self.certificate_content_base64)
        with open(cert_file, "wb") as f:
            f.write(certificate_content_bytes)
        return cert_folder

    @classmethod
    def get_benchmark_datasets_certificates(
        cls, benchmark_id: int
    ) -> Tuple[List[Certificate], dict[int, dict]]:
        # this api returns owners as dicts.
        cert_data_list = config.comms.get_benchmark_datasets_certificates(
            benchmark_id=benchmark_id, filters={"is_valid": True}
        )

        # Transfer user info to another dict
        users_mapping = dict()
        for cert_data in cert_data_list:
            users_mapping[cert_data["id"]] = cert_data["owner"]
            cert_data["owner"] = cert_data["owner"]["id"]

        cert_obj_list = [cls(**cert_data) for cert_data in cert_data_list]
        return cert_obj_list, users_mapping

    @classmethod
    def get_user_certificate(cls):
        user_id = get_medperf_user_data()["id"]
        user_certificates = Certificate.all(filters={"owner": user_id})
        user_certificates = [
            cert
            for cert in user_certificates
            if cert.ca == config.certificate_authority_id and cert.is_valid
        ]
        if len(user_certificates) == 0:
            return

        if len(user_certificates) > 1:
            raise MedperfException(
                "Internal Error: Multiple certificates has been found"
            )
        return user_certificates[0]

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
            "CA ID": self.ca,
            "Created At": self.created_at,
            "Is Valid": self.is_valid,
        }
