from cryptography import x509

from django.conf import settings
from .cryptography.ca import generate_root_cert, sign_certificate
from .cryptography.utils import cert_to_str, str_to_cert, str_to_csr
from training.models import TrainingExperiment


def __get_experiment_key_pair(training_exp_id):
    exp = TrainingExperiment.objects.get(pk=training_exp_id)
    private_key_id = exp.private_key
    private_key = settings.KEY_STORAGE.read(private_key_id)
    public_key_str = exp.public_key
    public_key = str_to_cert(public_key_str)
    return private_key, public_key


def generate_key_pair(training_exp_id):
    # TODO: do we need to destroy the keys at some point?
    ca_common_name = f"training_{training_exp_id}"
    root_private_key, certificate = generate_root_cert(ca_common_name)

    # store private key
    storage_id = ca_common_name
    settings.KEY_STORAGE.write(root_private_key, storage_id)

    # public key to str
    public_key_str = cert_to_str(certificate)
    return storage_id, public_key_str


def sign_csr(csr_str, training_exp_id):
    # Load CSR
    csr = str_to_csr(csr_str)

    # load signing key and crt
    signing_key, signing_crt = __get_experiment_key_pair(training_exp_id)

    # sign
    signed_cert = sign_certificate(csr, signing_key, signing_crt.subject)

    # cert as str
    cert_str = cert_to_str(signed_cert)

    return cert_str


def verify_dataset_csr(csr_str, dataset_object, training_exp):
    # TODO?
    try:
        csr = str_to_csr(csr_str)
    except ValueError as e:
        return False, str(e)
    if not isinstance(csr, x509.CertificateSigningRequest):
        return False, "Invalid CSR format"
    return True, ""


def verify_aggregator_csr(csr_str, aggregator_object, training_exp, request):
    # TODO?
    try:
        csr = str_to_csr(csr_str)
    except ValueError as e:
        return False, str(e)
    if not isinstance(csr, x509.CertificateSigningRequest):
        return False, "Invalid CSR format"
    return True, ""
