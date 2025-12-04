from medperf import config
from medperf.commands.certificate.utils import current_user_certificate_status


class CheckUserCertificate:
    @staticmethod
    def run():
        """check local cert folder and server certificate object"""
        status_dict = current_user_certificate_status()

        if status_dict["no_certs_found"]:
            config.ui.print("No certificates found.")
        elif status_dict["should_be_submitted"]:
            config.ui.print("Certificate exists locally. Certificate not submitted.")
        elif status_dict["should_be_invalidated"]:
            config.ui.print(
                "Certificate seems to be invalid. Consider deleting the certificate."
            )
        elif status_dict["no_action_required"]:
            config.ui.print("Certificate exists and is already submitted.")
