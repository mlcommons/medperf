from __future__ import annotations
from medperf.entities.cube import Cube
from medperf.entities.interface import Entity
from medperf.account_management import get_medperf_user_data
from medperf import config
from medperf.entities.ca import CA
from medperf.exceptions import MedperfException
from medperf.utils import generate_tmp_path
from pydantic import validator
import base64


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
        cert_file = generate_tmp_path()
        certificate_content_bytes = base64.b64decode(self.certificate_content_base64)
        with open(cert_file, "wb") as f:
            f.write(certificate_content_bytes)
        return cert_file

    @classmethod
    def get_benchmark_datasets_certificates(
        cls, benchmark_id: int
    ) -> list[Certificate]:
        cert_data_list = config.comms.get_benchmark_datasets_certificates(
            benchmark_id=benchmark_id, filters={"is_valid": True}
        )

        cert_obj_list = [cls(**cert_data) for cert_data in cert_data_list]
        return cert_obj_list

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

    def verify(self):  # TODO
        ca = CA.get(self.ca)
        ca_container = Cube.get(ca.ca_mlcube)
        cert_file = self.prepare_certificate_file()
        mounts = {"cert_file": cert_file}  # TODO
        env = {}  # TODO
        ca_container.run(
            task="verify_cert", mounts=mounts, env=env, disable_network=False
        )
