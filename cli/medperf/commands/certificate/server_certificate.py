from medperf.entities.ca import CA
from medperf.entities.aggregator import Aggregator
from medperf.certificates import get_server_cert
from medperf.exceptions import MedperfException
from medperf.utils import get_pki_assets_path, remove_path
from medperf import config
import os


class GetServerCertificate:
    @staticmethod
    def run(aggregator_id: int, ca_id: int = None, overwrite: bool = False):
        """get server cert"""
        ca_id = ca_id or config.certificate_authority_id
        ca = CA.get(ca_id)
        aggregator = Aggregator.get(aggregator_id)
        address = aggregator.address
        output_path = get_pki_assets_path(address, ca.name)
        if os.path.exists(output_path):
            if not overwrite:
                raise MedperfException(
                    "Cert and key already present. Rerun the command with --overwrite"
                )
            remove_path(output_path)
        get_server_cert(ca, address, output_path)
