import os
from medperf.entities.kbs import KBS


class RunAs:
    @classmethod
    def run(cls, as_id):
        kbs: KBS = KBS.get(as_id)
        kbs_port = kbs.config["kbs_port"]
        as_port = kbs.config["port"]
        rvps_port = kbs.config["rvps_port"]

        # create admin key
        script = os.path.join(os.path.dirname(__file__), "scripts/generate_cert.sh")
        os.system(f"bash {script} -c {kbs.admin_public_key_path} -k {kbs.admin_private_key_path}")

        kbs_command = [
            "docker",
            "run",
            "--rm",
            "--name",
            kbs.container_name,
            "-p",
            f"{kbs_port}:{kbs_port}",
            "-e",
            "RUST_LOG=debug",
            "-v",
            f"{kbs.kbs_storage}:/opt/confidential-containers/kbs/repository:rw",
            "-v",
            f"{kbs.admin_public_key_path}:/opt/confidential-containers/kbs/user-keys/public.pub",
            "-v",
            f"{kbs.kbs_config_path}:/etc/kbs-config.toml",
            "-v",
            f"{kbs.policy_path}:/opt/confidential-containers/kbs/policy.rego",
            "-v",
            f"{kbs.cert_path}:/etc/cert.pem",
            "-v",
            f"{kbs.key_path}:/etc/key.pem",
            "ghcr.io/confidential-containers/staged-images/kbs-grpc-as:68e2a8d25dbfa012b422ff464f31d18f3afa6677",
            "/usr/local/bin/kbs",
            "--config-file",
            "/etc/kbs-config.toml",
        ]

        as_command = [
            "docker",
            "run",
            "--rm",
            "--name",
            kbs.as_container_name,
            "-p",
            f"{as_port}:{as_port}",
            "-e",
            "RUST_LOG=debug",
            "-v",
            f"{kbs.attestation_service_folder}:/opt/confidential-containers/attestation-service:rw",
            "-v",
            f"{kbs.as_config_path}:/etc/as-config.json:rw",
            "-v",
            f"{kbs.qcnl_config_path}:/etc/sgx_default_qcnl.conf:rw",
            "-v",
            f"{kbs.verification_cert_path}:/etc/as-cert.pem",
            "-v",
            f"{kbs.verification_key_path}:/etc/as-key.pem",
            "ghcr.io/confidential-containers/staged-images/coco-as-grpc:68e2a8d25dbfa012b422ff464f31d18f3afa6677",
            "grpc-as",
            "--socket",
            f"0.0.0.0:{as_port}",
            "--config-file",
            "/etc/as-config.json",
        ]

        rvps_command = [
            "docker",
            "run",
            "--rm",
            "--name",
            kbs.rvps_container_name,
            "-p",
            f"{rvps_port}:{rvps_port}",
            "-e",
            "RUST_LOG=debug",
            "-v",
            f"{kbs.reference_values_folder}:/opt/confidential-containers/attestation-service/reference_values:rw",
            "-v",
            f"{kbs.rvps_config_path}:/etc/rvps.json:rw",
            "ghcr.io/confidential-containers/staged-images/rvps:68e2a8d25dbfa012b422ff464f31d18f3afa6677",
            "rvps",
            "--address",
            f"0.0.0.0:{rvps_port}",
        ]

        os.system(" ".join(rvps_command))
        os.system(" ".join(as_command))
        os.system(" ".join(kbs_command))
