from medperf.utils import get_file_hash
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from pydantic import BaseModel
import datetime
from cryptography.x509 import Certificate as X509Certificate
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding
from ipaddress import IPv4Address


class TestCertificateInfo(BaseModel):
    certificate_obj: X509Certificate
    private_key: rsa.RSAPrivateKey

    @property
    def certificate_bytes(self) -> bytes:
        return self.certificate_obj.public_bytes(encoding=Encoding.PEM)

    class Config:
        arbitrary_types_allowed = True


def calculate_fake_file_hash(fs, contents):
    # TODO: should calculate the hash of a string in memory
    fs.create_file("some_file", contents=contents)
    return get_file_hash("some_file")


def generate_test_certificate(root_certificate_info: Optional[TestCertificateInfo] = None) -> TestCertificateInfo:
    """
    Simple function to generate either a root certificate or a certificate
    signed by a root certificate. Used in some tests.
    """
    private_cert_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "TestProvince"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "TestVille"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MLCommons Testing"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).public_key(
        private_cert_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=3)
    )

    if not root_certificate_info:
        # This is the root certificate. Add relevant extensions and self-sign.
        cert = cert.issuer_name(
            subject
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_cert_key.public_key()),
            critical=False,
        ).sign(private_cert_key, hashes.SHA256())
    else:
        root_cert = root_certificate_info.certificate_obj
        root_private_key = root_certificate_info.private_key

        cert = cert.issuer_name(
            root_cert.subject
        ).add_extension(
            x509.SubjectAlternativeName([
                # Describe what sites we want this certificate for.
                x509.DNSName("localhost"),
                x509.IPAddress(IPv4Address('192.168.0.1')),
                x509.IPAddress(IPv4Address('127.0.0.1')),
                x509.IPAddress(IPv4Address('0.0.0.0')),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_cert_key.public_key()),
            critical=False,
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                root_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
            ),
            critical=False,
        ).sign(root_private_key, hashes.SHA256())

    return TestCertificateInfo(certificate_obj=cert, private_key=private_cert_key)
