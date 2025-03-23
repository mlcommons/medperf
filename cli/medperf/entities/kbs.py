from medperf.entities.interface import Entity
import medperf.config as config
import os


class KBS(Entity):
    """
    Class representing a Result entry

    Results are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark results and how to upload them to the backend.
    """

    config: dict
    kbs_type: str
    metadata: dict = {}

    @staticmethod
    def get_type():
        return "kbs"

    @staticmethod
    def get_storage_path():
        return config.kbs_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_kbs

    @staticmethod
    def get_metadata_filename():
        return config.kbs_info_file

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_kbs

    def __init__(self, *args, **kwargs):
        """Creates a new result instance"""
        super().__init__(*args, **kwargs)
        self.private_path = os.path.join(config.kbs_keys_path, str(self.id))
        self.cert_path = os.path.join(self.path, "kbs.crt")
        self.key_path = os.path.join(self.private_path, "kbs.key")

        self.verification_cert_path = os.path.join(self.path, "as.crt")
        self.verification_key_path = os.path.join(self.private_path, "verif.key")

        self.admin_public_key_path = os.path.join(self.private_path, "admin.pub")
        self.admin_private_key_path = os.path.join(self.private_path, "admin.key")

        self.kbs_config_path = os.path.join(self.path, "kbs_config.toml")
        self.as_config_path = os.path.join(self.path, "as_config.json")
        self.rvps_config_path = os.path.join(self.path, "rvps.json")
        self.policy_path = os.path.join(self.path, "policy.rego")
        self.qcnl_config_path = os.path.join(self.path, "qcnl.conf")

        self.kbs_storage = os.path.join(config.kbs_storage, str(self.id))
        self.container_name = f"kbs_{self.id}"
        self.as_container_name = f"as_{self.id}"
        self.rvps_container_name = f"rvps_{self.id}"

        self.attestation_service_folder = os.path.join(self.path, "attestation_service")
        self.reference_values_folder = os.path.join(self.path, "reference_values")

    @classmethod
    def get(cls, uid, local_only=False):
        kbs = super().get(uid, local_only)
        kbs.write_cert()
        kbs.write_verification_cert()
        kbs.write_default_policy()
        kbs.write_config()

    @property
    def local_id(self):
        return self.name

    def write_cert(self):
        cert = self.config["cert"]
        with open(self.cert_path, "w") as f:
            f.write(cert)

    def write_verification_cert(self):
        if self.kbs_type != "as":
            return
        verification_cert = self.config["verification_cert"]
        with open(self.verification_cert_path, "w") as f:
            f.write(verification_cert)

    def write_default_policy(self):
        if os.path.exists(self.policy_path):
            return
        with open(config.kbs_default_policy_template_path) as f:
            policy_text = f.read()
        with open(self.policy_path, "w") as f:
            f.write(policy_text)

    def write_config(self):
        if self.kbs_type == "as":
            self._write_as_config()
        else:
            self._write_kbs_config()

    def _write_kbs_config(self):
        with open(config.kbs_config_template_path) as f:
            contents = f.read()
        as_obj: KBS = KBS.get(self.config["as"])
        contents = contents.format(
            kbs_port=self.config["port"],
            as_url=as_obj.config["address"],
            as_port=as_obj.config["port"],
        )
        with open(self.kbs_config_path, "w") as f:
            f.write(contents)

    def _write_as_config(self):
        with open(config.as_kbs_config_template_path) as f:
            contents = f.read()
        contents = contents.format(
            kbs_port=self.config["kbs_port"],
            as_url=self.config["address"],
            as_port=self.config["port"],
        )
        with open(self.kbs_config_path, "w") as f:
            f.write(contents)

        ######################

        with open(config.as_config_template_path) as f:
            contents = f.read()
        contents = contents.format(
            rvps_url=self.config["address"],
            rvps_port=self.config["rvps_port"],
        )
        with open(self.as_config_path, "w") as f:
            f.write(contents)

        ######################

        with open(config.rvps_config_template_path) as f:
            contents = f.read()
        with open(self.rvps_config_path, "w") as f:
            f.write(contents)

        ######################

        with open(config.qcnl_template_path) as f:
            contents = f.read()
        with open(self.qcnl_config_path, "w") as f:
            f.write(contents)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Created At": self.created_at,
            "Config": self.config,
            "Type": self.kbs_type,
        }
