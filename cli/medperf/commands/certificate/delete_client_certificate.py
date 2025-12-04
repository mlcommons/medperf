from medperf.account_management import get_medperf_user_data
from medperf.exceptions import CleanExit
from medperf.utils import approval_prompt, get_pki_assets_path, remove_path
from medperf import config
from medperf.entities.certificate import Certificate
import logging


class DeleteCertificate:
    @staticmethod
    def run(approved: bool = False):
        """delete local cert folder and invalidate server certificate object"""

        msg = "Please confirm that you would like to delete your current certificate."
        msg += " This action cannot be undone."
        msg += " [Y/n]"
        approved = approved or approval_prompt(msg)
        if not approved:
            raise CleanExit("Certificate deletion cancelled.")

        # Invalidate server certificate object
        cert = Certificate.get_user_certificate()
        if cert is not None:
            logging.debug("Found a remote certificate. Invalidating the certificate.")
            body = {"is_valid": False}
            config.comms.update_certificate(cert.id, body)

        # Delete local certificate folder
        email = get_medperf_user_data()["email"]
        local_cert_folder = get_pki_assets_path(email, config.certificate_authority_id)
        remove_path(local_cert_folder, sensitive=True)
