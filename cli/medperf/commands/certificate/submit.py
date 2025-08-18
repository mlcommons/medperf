from medperf.account_management import get_medperf_user_data
from medperf.exceptions import InvalidArgumentError
from medperf.utils import get_pki_assets_path, approval_prompt
import os
from medperf import config
from medperf.ui.interface import UI
from medperf.entities.certificate import Certificate
from medperf.certificates import trust
from medperf.commands.certificate.utils import get_ca_from_id_model_or_training_exp
from typing import Optional


class SubmitCertificate:
    @classmethod
    def run(cls, name: str, ca_id: Optional[int] = None, model_id: Optional[int] = None, training_exp_id: Optional[int] = None, approved: bool = False):
        """Upload certificate to MedPerf server"""
        current_ui: UI = config.ui
        submission = cls(name, ca_id, model_id, training_exp_id)

        msg = "When submitting your Certificate, your e-mail will be visible to the Model Owner(s) "
        msg += "that use the same Certificate Authority (CA) to grant private model access.\n"
        msg += "Do you wish to proceed? [Y/n]"

        approved = approved or approval_prompt(msg)

        if not approved:
            current_ui.print("Aggregator association operation cancelled.")
            return

        with current_ui.interactive():
            current_ui.text = "Submitting Certificate to MedPerf"
            submission.validate_certificate()
            updated_certificate_body = submission.submit()
        current_ui.print("Certificate uploaded")
        submission.write(updated_certificate_body)

    def __init__(self, name: str, ca_id: Optional[int] = None, model_id: Optional[int] = None, training_exp_id: Optional[int] = None):
        self.ui: UI = config.ui

        self.ca = get_ca_from_id_model_or_training_exp(ca_id=ca_id, model_id=model_id, training_exp_id=training_exp_id)

        email = get_medperf_user_data()["email"]
        pki_assets_path = get_pki_assets_path(email, self.ca.name)
        certificate_file_path = os.path.join(pki_assets_path, config.certificate_file)

        if not os.path.exists(certificate_file_path):
            raise InvalidArgumentError(
                f"No local certificate found for CA {self.ca.name} ({self.ca.id}). "
                "Please run the 'medperf certificate get_client_certificate' "
                "command to obtain a certificate before running the submit command."
            )

        with open(certificate_file_path, "r") as certificate_f:
            certificate_content = certificate_f.read()

        self.certificate = Certificate(
            name=name, ca_id=ca_id, certificate_content=certificate_content
        )

    def validate_certificate(self):
        trust(self.ca)

    def submit(self):
        updated_body = self.certificate.upload()
        return updated_body

    def write(self, updated_body):
        certificate = Certificate(**updated_body)
        certificate.write()
