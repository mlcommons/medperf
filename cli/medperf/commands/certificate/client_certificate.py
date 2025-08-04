from medperf.entities.ca import CA
from medperf.account_management import get_medperf_user_data
from medperf.certificates import get_client_cert
from medperf.exceptions import MedperfException
from medperf.utils import get_pki_assets_path, remove_path
import os
from medperf.exceptions import InvalidArgumentError


class GetUserCertificate:
    @staticmethod
    def run(
        training_exp_id: int = None, container_id: int = None, overwrite: bool = False
    ):
        """get user cert"""

        if training_exp_id:
            ca = CA.from_experiment(training_exp_id)
        elif container_id:
            ca = CA.from_container(container_id)
        else:
            # This is validated in the CLI, but better keep a check here to be extra safe
            raise InvalidArgumentError(
                "Exactly one of training_exp_id or container_id must be provided!"
            )

        email = get_medperf_user_data()["email"]
        output_path = get_pki_assets_path(email, ca.name)
        if os.path.exists(output_path):
            if not overwrite:
                raise MedperfException(
                    "Cert and key already present. Rerun the command with --overwrite"
                )
            remove_path(output_path)
        get_client_cert(ca, email, output_path)
