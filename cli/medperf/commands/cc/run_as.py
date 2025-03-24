from medperf.entities.kbs import KBS
from medperf import config
import subprocess


class RunAs:
    @classmethod
    def run(cls, as_id):
        kbs: KBS = KBS.get(as_id)
        kbs_port = kbs.config["kbs_port"]
        as_port = kbs.config["port"]
        rvps_port = kbs.config["rvps_port"]

        with open(config.as_compose_template_path) as f:
            contents = f.read()

        contents = contents.format(
            kbs_port=kbs_port,
            kbs_storage=kbs.kbs_storage,
            admin_public_key_path=kbs.admin_public_key_path,
            kbs_config_path=kbs.kbs_config_path,
            policy_path=kbs.policy_path,
            cert_path=kbs.cert_path,
            key_path=kbs.key_path,
            as_port=as_port,
            attestation_service_folder=kbs.attestation_service_folder,
            as_config_path=kbs.as_config_path,
            qcnl_config_path=kbs.qcnl_config_path,
            verification_cert_path=kbs.verification_cert_path,
            verification_key_path=kbs.verification_key_path,
            rvps_port=rvps_port,
            reference_values_folder=kbs.reference_values_folder,
            rvps_config_path=kbs.rvps_config_path,
        )

        with open(kbs.compose_path, "w") as f:
            f.write(contents)

        command = ["docker", "compose", "up", "-d"]
        subprocess.check_call(command, cwd=kbs.path)
