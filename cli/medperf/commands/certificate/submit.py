import base64
import uuid
from medperf.account_management import get_medperf_user_data
from medperf.exceptions import CleanExit, MedperfException
from medperf.utils import get_pki_assets_path, approval_prompt
import os
from medperf import config
from medperf.ui.interface import UI
from medperf.entities.certificate import Certificate
from medperf.certificates import verify_certificate
from medperf.enums import CryptoKeyType


class SubmitCertificate:
    @classmethod
    def run(cls, key_type: CryptoKeyType, approved: bool = False):
        """Upload certificate to MedPerf server"""
        ui: UI = config.ui
        submission = cls(key_type, approved)

        submission.prepare()
        with ui.interactive():
            ui.text = "Verifying Certificate"
            submission.verify_user_certificate()
        updated_certificate_body = submission.submit()
        ui.print("Certificate uploaded")
        submission.write(updated_certificate_body)

    def __init__(self, key_type: CryptoKeyType, approved: bool = False):
        self.ca_id = config.certificate_authority_id
        self.key_type = key_type
        self.approved = approved

    def prepare(self):
        self.__prepare_cert_object()

    def __prepare_cert_object(self):
        email = get_medperf_user_data()["email"]
        pki_assets_path = get_pki_assets_path(email, self.ca_id, key_type=self.key_type)
        certificate_file_path = os.path.join(pki_assets_path, config.certificate_file)

        if not os.path.exists(certificate_file_path):
            raise MedperfException(
                "No local certificate found. "
                "Please run the 'medperf certificate get_client_certificate' "
                "command to obtain a certificate before running the submit command."
            )

        with open(certificate_file_path, "rb") as f:
            certificate_content = f.read()
        cert_content_base64 = base64.b64encode(certificate_content).decode("utf-8")
        name = self.__generate_name()
        self.certificate = Certificate(
            name=name,
            ca=self.ca_id,
            certificate_content_base64=cert_content_base64,
            key_type=self.key_type,
        )

    def __generate_name(self):
        return uuid.uuid4().hex

    def verify_user_certificate(self):
        email = get_medperf_user_data()["email"]
        verify_certificate(self.certificate, expected_cn=email)

    def submit(self):
        msg = "When submitting your Certificate, your e-mail will be visible to the Model Owner(s) "
        msg += "that belong to benchmarks your datasets are part of.\n"
        msg += "Do you wish to proceed? [Y/n]"

        approved = self.approved or approval_prompt(msg)

        if not approved:
            raise CleanExit("Certificate submission cancelled")
        updated_body = self.certificate.upload()
        return updated_body

    def write(self, updated_body):
        certificate = Certificate(**updated_body)
        certificate.write()
