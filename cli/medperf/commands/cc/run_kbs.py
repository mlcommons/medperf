import os
from medperf.entities.kbs import KBS


class RunKbs:
    @classmethod
    def run(cls, kbs_id):
        kbs: KBS = KBS.get(kbs_id)
        port = kbs.config["port"]
        kbs_as: KBS = KBS.get(kbs.config["as"])

        docker_args = [
            "docker",
            "run",
            "-d",
            "--name",
            f"{kbs.container_name}",
            "-p",
            f"{port}:{port}",
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
            "-v",
            f"{kbs_as.verification_cert_path}:/etc/as-cert.pem",
            "ghcr.io/confidential-containers/staged-images/kbs-grpc-as:68e2a8d25dbfa012b422ff464f31d18f3afa6677",
            "/usr/local/bin/kbs",
            "--config-file",
            "/etc/kbs-config.toml",
        ]
        os.system(" ".join(docker_args))
