from medperf.entities.ca import CA
from medperf.account_management import get_medperf_user_data
from medperf.certificates import get_client_cert
from medperf.utils import get_pki_assets_path
import os


class GetUserCertificate:
    @staticmethod
    def run(training_exp_id: int):
        """get user cert"""
        ca = CA.from_experiment(training_exp_id)
        email = get_medperf_user_data()["email"]
        output_path = get_pki_assets_path(email, ca.name)
        if os.path.exists(output_path) and os.listdir(output_path):
            # TODO?
            raise ValueError("already")
        get_client_cert(ca, email, output_path)
