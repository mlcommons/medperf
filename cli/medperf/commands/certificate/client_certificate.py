from medperf.account_management import get_medperf_user_data
from medperf.certificates import get_client_cert
from medperf.exceptions import MedperfException
from medperf.ui.interface import UI
from medperf.utils import get_pki_assets_path, remove_path
from medperf import config
from medperf.entities.ca import CA
import os


class GetUserCertificate:
    @staticmethod
    def run(overwrite: bool = False):
        """get user cert"""
        ui: UI = config.ui
        ca_id = config.certificate_authority_id
        ca = CA.get(ca_id)

        email = get_medperf_user_data()["email"]
        output_path = get_pki_assets_path(email, ca.id)
        if os.path.exists(output_path):
            if not overwrite:
                raise MedperfException(
                    "Cert and key already present. Rerun the command with --overwrite"
                )
            remove_path(output_path, sensitive=True)

        with ui.interactive():
            ui.text = "Getting Certificate"
            with ui.parsed_output():
                get_client_cert(ca, email, output_path)
