import base64
import uuid
from medperf.entities.certificate import Certificate
from medperf.entities.ca import CA
from medperf.utils import (
    approval_prompt,
    get_decryption_key_path,
    validate_and_normalize_emails,
)
from medperf import config
from medperf.exceptions import CleanExit, InvalidCertificateError
from medperf.entities.encrypted_container_key import EncryptedKey
from medperf.encryption import AsymmetricEncryption
from medperf.certificates import verify_certificate_authority, verify_certificate
import logging


class GrantAccess:
    @classmethod
    def run(
        cls,
        benchmark_id: int,
        model_id: int,
        approved: bool = False,
        allowed_emails: str = None,
    ):
        """
        Registers encrypted access keys in the MedPerf server for all
        Data Owners registered to the Benchmark from benchmark_id and
        authorized by the Certificate Authority from ca_id.

        allowed_emails: a string containing space-separated list of emails
        """
        grantaccess = cls(benchmark_id, model_id, approved, allowed_emails)
        grantaccess.get_approval()
        grantaccess.validate_allowed_emails()
        grantaccess.verify_certificate_authority()
        grantaccess.prepare_certificates_list()
        grantaccess.filter_certificates()
        grantaccess.verify_certificates()
        keys = grantaccess.generate_encrypted_keys_list()
        grantaccess.upload(keys)

    def __init__(
        self,
        benchmark_id: int,
        model_id: int,
        approved: bool = False,
        allowed_emails: list = None,
    ):
        self.benchmark_id = benchmark_id
        self.model_id = model_id
        self.approved = approved
        self.allowed_emails = allowed_emails
        self.certificates = None
        self.cert_user_info = None

    def get_approval(self):
        msg = (
            f"Please confirm that you wish to give all Data Owners "
            f"registered in Benchmark (UID: {self.benchmark_id}) access to "
            f"the Model (UID: {self.model_id}).\n"
        )

        if not self.approved and not approval_prompt(msg):
            raise CleanExit("Access granting operation cancelled")

    def validate_allowed_emails(self):
        if self.allowed_emails is not None:
            self.allowed_emails = self.allowed_emails.strip().split(" ")
            self.allowed_emails = validate_and_normalize_emails(self.allowed_emails)

    def verify_certificate_authority(self):
        config.ui.print("Verifying Certificate Authority")
        ca = CA.get(uid=config.certificate_authority_id)
        verify_certificate_authority(
            ca, expected_fingerprint=config.certificate_authority_fingerprint
        )

    def prepare_certificates_list(self):
        config.ui.print("Getting Data Owner Certificates")
        certificates, cert_user_info = Certificate.get_benchmark_datasets_certificates(
            self.benchmark_id
        )
        existing_keys = EncryptedKey.get_container_keys(self.model_id)
        certificates_with_keys = [key.certificate for key in existing_keys]

        certificates_need_keys: list[Certificate] = []

        for cert in certificates:
            if cert.id not in certificates_with_keys:
                certificates_need_keys.append(cert)

        logging.debug(f"Available Certificates: {[cert.id for cert in certificates]}")
        logging.debug(f"Certificates already have access: {certificates_with_keys}")
        logging.debug(
            f"Certificates that need access: {[cert.id for cert in certificates_need_keys]}"
        )
        if not certificates_need_keys:
            raise CleanExit("No users in need of keys were found.")

        self.certificates = certificates_need_keys
        self.cert_user_info = cert_user_info

    def filter_certificates(self):
        if self.allowed_emails is None:
            return
        logging.debug("Filtering certificates based on allowed emails list")
        filtered_certificates = []
        for certificate in self.certificates:
            email = self.cert_user_info[certificate.id]["email"]
            if email in self.allowed_emails:
                filtered_certificates.append(certificate)

        logging.debug(
            f"Certificates after filtering: {[cert.id for cert in filtered_certificates]}"
        )
        if not filtered_certificates:
            raise CleanExit("No allowed filtered users in need of keys were found.")

        self.certificates = filtered_certificates

    def verify_certificates(self):
        error_certs = []
        valid_certs = []

        for certificate in self.certificates:
            expected_email = self.cert_user_info[certificate.id]["email"]
            try:
                verify_certificate(
                    certificate, expected_cn=expected_email, verify_ca=False
                )
                valid_certs.append(certificate)
            except InvalidCertificateError:
                logging.debug(f"Invalid Certificate: {certificate.id}")
                error_certs.append((certificate, expected_email))

        if error_certs:
            error_cert_msg = "The following certificates failed verification:\n"
            for error_cert, expected_email in error_certs:
                error_cert_msg += (
                    f"\t(UID:{error_cert.id}, Expected Owner: {expected_email})\n"
                )
            config.ui.print(error_cert_msg)

        if not valid_certs:
            raise CleanExit(
                "No users with valid certificates in need of keys were found."
            )

        self.certificates = valid_certs

    def generate_encrypted_keys_list(self):
        encryptor = AsymmetricEncryption()
        keys_objects = []
        container_key_file = get_decryption_key_path(self.model_id)
        with open(container_key_file, "rb") as f:
            container_key_bytes = f.read()

        for certificate in self.certificates:
            certificate_content_bytes = base64.b64decode(
                certificate.certificate_content_base64
            )
            encrypted_key_bytes = encryptor.encrypt(
                certificate_content_bytes, container_key_bytes
            )
            key_name = f"M{self.model_id}C{certificate.id}_" + uuid.uuid4().hex
            key_obj = EncryptedKey(
                encrypted_key_base64=base64.b64encode(encrypted_key_bytes).decode(),
                name=key_name,
                certificate=certificate.id,
                container=self.model_id,
            )
            keys_objects.append(key_obj)
        return keys_objects

    def upload(self, keys_objects):
        config.ui.print("Uploading Encrypted Keys")
        EncryptedKey.upload_many(keys_objects)
