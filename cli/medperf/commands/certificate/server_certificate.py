from medperf.entities.ca import CA
from medperf.entities.aggregator import Aggregator
from medperf.certificates import get_server_cert
from medperf.exceptions import MedperfException
from medperf.utils import get_pki_assets_path, remove_path
import os


class GetServerCertificate:
    @staticmethod
    def run(training_exp_id: int, overwrite: bool = False):
        """get server cert"""
        ca = CA.from_experiment(training_exp_id)
        aggregator = Aggregator.from_experiment(training_exp_id)
        address = aggregator.address
        output_path = get_pki_assets_path(address, ca.name)
        if os.path.exists(output_path):
            if not overwrite:
                raise MedperfException(
                    "Cert and key already present. Rerun the command with --overwrite"
                )
            remove_path(output_path)
        get_server_cert(ca, address, output_path)
