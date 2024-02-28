from cryptography.hazmat.primitives import serialization
from cryptography import x509


def cert_to_str(cert):
    return cert.public_bytes(encoding=serialization.Encoding.PEM).decode("utf-8")


def str_to_cert(cert_str):
    return x509.load_pem_x509_certificate(cert_str.encode("utf-8"))


def str_to_csr(csr_str):
    return x509.load_pem_x509_csr(csr_str.encode("utf-8"))
