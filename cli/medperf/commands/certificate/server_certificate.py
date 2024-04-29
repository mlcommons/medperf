from medperf.entities.ca import CA
from medperf.entities.aggregator import Aggregator
from medperf.certificates import get_server_cert
from medperf.utils import get_pki_assets_path
import os


class GetServerCertificate:
    @staticmethod
    def run(training_exp_id: int):
        """get server cert"""
        ca = CA.from_experiment(training_exp_id)
        aggregator = Aggregator.from_experiment(training_exp_id)
        address = aggregator.address
        output_path = get_pki_assets_path(address, ca.name)
        if os.path.exists(output_path) and os.listdir(output_path):
            # TODO?
            raise ValueError("already")
        get_server_cert(ca, address, output_path)
