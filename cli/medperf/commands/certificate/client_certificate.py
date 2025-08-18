from medperf.account_management import get_medperf_user_data
from medperf.certificates import get_client_cert
from medperf.exceptions import MedperfException
from medperf.utils import get_pki_assets_path, remove_path
import os
from medperf.commands.certificate.utils import get_ca_from_id_model_or_training_exp


class GetUserCertificate:
    @staticmethod
    def run(
        training_exp_id: int = None, model_id: int = None, ca_id: int = None, overwrite: bool = False
    ):
        """get user cert"""
        ca = get_ca_from_id_model_or_training_exp(ca_id=ca_id, model_id=model_id, training_exp_id=training_exp_id)

        email = get_medperf_user_data()["email"]
        output_path = get_pki_assets_path(email, ca.name)
        if os.path.exists(output_path):
            if not overwrite:
                raise MedperfException(
                    "Cert and key already present. Rerun the command with --overwrite"
                )
            remove_path(output_path)
        get_client_cert(ca, email, output_path)
