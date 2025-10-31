import base64
from medperf.entities.certificate import Certificate
from medperf.entities.ca import CA
from medperf.utils import approval_prompt, get_decryption_key_path
from medperf import config
from medperf.exceptions import CleanExit, InvalidCertificateError
from medperf.entities.encrypted_container_key import EncryptedContainerKey
from medperf.encryption import AsymmetricEncryption


class GrantAccess:
    @classmethod
    def run(
        cls,
        benchmark_id: int,
        model_id: int,
        approved: bool = False,
    ):
        """
        Registers encrypted access keys in the MedPerf server for all
        Data Owners registered to the Benchmark from benchmark_id and
        authorized by the Certificate Authority from ca_id.
        """
        grantaccess = cls(benchmark_id, model_id, approved)
        grantaccess.get_approval()
        grantaccess.verify_certificate_authority()
        grantaccess.prepare_certificates_list()
        grantaccess.verify_certificates()
        keys = grantaccess.generate_encrypted_keys_list()
        grantaccess.upload(keys)

    def __init__(
        self,
        benchmark_id: int,
        model_id: int,
        approved: bool = False,
    ):
        self.benchmark_id = benchmark_id
        self.model_id = model_id
        self.approved = approved

    def get_approval(self):
        msg = (
            f"Please confirm that you wish to give *ALL* Data Owners "
            f"registered in Benchmark (UID: {self.benchmark_id}) access to "
            f"the Model (UID: {self.model_id}).\n"
        )

        if not self.approved and not approval_prompt(msg):
            raise CleanExit("Access granting operation cancelled")

    def verify_certificate_authority(self):
        config.ui.print("Verifying Certificate Authority")
        ca = CA.get(uid=config.certificate_authority_id)
        ca.verify()

    def prepare_certificates_list(self):
        config.ui.print("Getting Data Owner Certificates")
        certificates, cert_user_info = Certificate.get_benchmark_datasets_certificates(
            self.benchmark_id
        )
        existing_keys = EncryptedContainerKey.get_user_keys()
        certificates_with_keys = [key["certificate"] for key in existing_keys]

        certificates_need_keys: list[Certificate] = list()

        for cert in certificates:
            if cert.id not in certificates_with_keys:
                certificates_need_keys.append(cert)

        if not certificates_need_keys:
            raise CleanExit("No users in need of keys were found.")

        self.certificates = certificates_need_keys
        self.cert_user_info = cert_user_info

    def verify_certificates(self):
        error_certs = []
        valid_certs = []

        for certificate in self.certificates:
            expected_email = self.cert_user_info[certificate.id]["email"]
            try:
                certificate.verify(expected_cn=expected_email, verify_ca=False)
                valid_certs.append(certificate)
            except InvalidCertificateError:
                error_certs.append(certificate)

        if error_certs:
            error_cert_msg = "The following certificates failed verification:\n"
            for error_cert in error_certs:
                error_cert_msg += f"{error_cert.name} (UID:{error_cert.id}, Owner: {error_cert.owner})\n"
            config.ui.print(error_cert_msg)

        self.certificates = valid_certs

    def generate_encrypted_keys_list(self):
        encryptor = AsymmetricEncryption()
        keys_objects = []
        container_key_file = get_decryption_key_path(self.model_id)
        with open(container_key_file, "rb") as f:
            container_key_bytes = f.read()

        for certificate in self.certificates:
            certificate_content_bytes = base64.b64decode(
                certificate.certificate_content_base64
            )
            encrypted_key_bytes = encryptor.encrypt(
                certificate_content_bytes, container_key_bytes
            )
            key_obj = EncryptedContainerKey(
                encrypted_key_base64=base64.b64encode(encrypted_key_bytes).decode(),
                name=f"Model {self.model_id} cert {certificate.id}",
                certificate=certificate.id,
                container=self.model_id,
            )
            del encrypted_key_bytes
            keys_objects.append(key_obj)
        del container_key_bytes
        return keys_objects

    def upload(self, keys_objects):
        config.ui.print("Uploading Encrypted Keys")
        EncryptedContainerKey.upload_many(keys_objects)
        del keys_objects
