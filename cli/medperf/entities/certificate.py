from __future__ import annotations
from medperf.entities.interface import Entity
from medperf.account_management import get_medperf_user_data
from medperf.utils import get_pki_assets_path
from medperf import config
from typing import Optional
from medperf.entities.ca import CA
from medperf.certificates import trust
from pydantic import root_validator, Field
from typing import Any
import base64
import os
from cryptography.x509 import UnsupportedGeneralNameType, load_pem_x509_certificate
from cryptography.x509.verification import PolicyBuilder, Store, VerificationError
from medperf.exceptions import InvalidCertificateError


class Certificate(Entity):
    """
    Class representing a Certificate uploaded to the MedPerf server
    Currently only supports Client Certificates (ie common name is a email)
    """

    certificate_content_base64: Optional[str]
    certificate_content: Optional[bytes] = Field(exclude=True)
    ca: int
    ca_name: Optional[str]

    @root_validator(pre=False)
    def validate_certificate_content(cls, values: dict[str, Any]):
        """
        If only one of certificate_content_base64 or certificate_content is provided,
        generate the other one via base64 encoding/decoding.
        If both are provided, verify they match. If not, raise a ValueError.
        If neither is provided, raise a ValueError.
        """
        content_base64 = values.get("certificate_content_base64")
        content: bytes = values.get("certificate_content")
        if content_base64 is None and content is None:
            raise ValueError(
                "One of certificate_content_base64 or certificate_content must be provided!"
            )

        elif content is not None:
            converted_content = base64.b64encode(content).decode("utf-8")
            if content_base64 is None:
                values["certificate_content_base64"] = converted_content

            elif converted_content != content_base64:
                raise ValueError(
                    "The values provided for certificate_content and certificate_content_base64 do not match!"
                )

        elif content_base64 is not None:
            converted_base64 = base64.b64decode(content_base64)
            values["certificate_content"] = converted_base64

        return values

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
            ca = CA.get(self.ca)
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
            "CA ID": self.ca,
            "State": self.state,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }

    def verify_with_ca(self, ca: CA, validate_ca: bool = True,
                       intermediate_certificates: Optional[list[Certificate]] = None):
        if validate_ca:
            trust(ca)

        if intermediate_certificates is None:
            intermediate_certificates = []

        intermediates = [load_pem_x509_certificate(cert.certificate_content)
                         for cert in intermediate_certificates]

        this_certificate = load_pem_x509_certificate(self.certificate_content)

        ca_cert_path = os.path.join(ca.pki_assets, config.ca_certificate_file)
        with open(ca_cert_path, 'rb') as ca_cert:
            loaded_cert = load_pem_x509_certificate(ca_cert.read())
            store = Store([loaded_cert])
        builder = PolicyBuilder().store(store)
        verifier = builder.build_client_verifier()

        try:
            verifier.verify(this_certificate, intermediates=intermediates)
            return True
        except (VerificationError, UnsupportedGeneralNameType) as e:
            error_msg = (
                f'Certificate could not be validated with '
                f'CA {ca.name} (UID: {ca.id}). Details:\n{str(e)}'
            )
            raise InvalidCertificateError(error_msg)
