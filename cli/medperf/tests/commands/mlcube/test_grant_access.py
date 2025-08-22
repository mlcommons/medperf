from __future__ import annotations
import pytest
from pytest_mock import MockerFixture
from typing import TYPE_CHECKING
from medperf.entities.cube import Cube
from medperf.entities.ca import CA
from medperf.commands.mlcube.grant_access import GrantAccess
from pathlib import Path
from medperf import config
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
from cryptography import x509
from cryptography.x509.oid import NameOID
from medperf.entities.certificate import Certificate
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime


if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


PATCH_ASSOC = "medperf.commands.mlcube.grant_access.{}"
NUM_MOCK_CERTS = 2
MOCK_CERTIFICATE_CONTENTS = [b'some content', b'another content']


@pytest.fixture
def mock_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )


@pytest.fixture
def mock_certificate_bytes(mock_private_key: rsa.RSAPrivateKey) -> bytes:

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test Province"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Test Ville"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MLCommons"),
        x509.NameAttribute(NameOID.COMMON_NAME, "mlcommons.medperf.test.com"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        mock_private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False,
    ).sign(mock_private_key, hashes.SHA256())
    return cert.public_bytes(encoding=serialization.Encoding.PEM)


@pytest.fixture()
def mock_padding() -> padding.AsymmetricPadding:
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )


@pytest.fixture
def cube(mocker: MockerFixture):
    cube = mocker.create_autospec(spec=Cube)
    mocker.patch.object(Cube, "get", return_value=cube)
    cube.name = "name"
    return cube


@pytest.fixture
def mock_ca() -> CA:
    ca = CA(id=10, name='TestCA', owner=None, for_test=True,
            server_mlcube=1, client_mlcube=1, ca_mlcube=1, ca_dict={},
            config={'address': 'www.test.com', 'port': '1234', 'fingerprint': '',
                    'client_provisioner': '', 'server_provisioner': ''})
    return ca


@pytest.fixture
def mock_certificate_list() -> list[Certificate]:

    mock_cert_list = []
    for i, content in enumerate(MOCK_CERTIFICATE_CONTENTS):
        mock_cert = Certificate(id=i + 1,
                                name='TestCert',
                                owner=i + 2,
                                for_test=True,
                                certificate_content=content,
                                ca_id=10)
        mock_cert_list.append(mock_cert)
    return mock_cert_list


@pytest.fixture
def mock_container_key_file(mocker: MockerFixture, fs: FakeFilesystem) -> Path:
    # Fake directory for fake key
    fake_dir = Path('/path/to/fake/')
    mocker.patch(PATCH_ASSOC.format('get_container_key_dir_path'),
                 return_value=str(fake_dir))
    fake_key_file_path = fake_dir / config.container_key_file
    fs.create_file(fake_key_file_path, contents=b'somekey')
    return fake_key_file_path


@pytest.fixture
def mock_container_key_bytes(mocker: MockerFixture):
    key = Fernet.generate_key()
    return key


def test_grant_access_flow(mocker: MockerFixture, mock_ca: CA, mock_container_key_file: Path,
                           mock_certificate_list: list[Certificate]):

    mocker.patch.object(CA, 'get', return_value=mock_ca)
    mocker.patch(PATCH_ASSOC.format('trust'))
    spy_get_list = mocker.patch.object(Certificate, 'get_list_from_benchmark_model_ca',
                                       return_value=mock_certificate_list)
    spy_verify = mocker.patch.object(Certificate, 'verify_with_ca')
    spy_generate_encrypted_keys_list = mocker.patch.object(
        GrantAccess, 'generate_encrypted_keys_list',
        return_value=['key1', 'key2'])
    spy_upload_many = mocker.patch(PATCH_ASSOC.format('EncryptedContainerKey.upload_many'))
    GrantAccess.run(ca_id=mock_ca.id, model_id=1, benchmark_id=1,
                    name='TestAccess', approved=True)

    spy_get_list.assert_called_once()
    assert spy_verify.call_count == len(mock_certificate_list)
    spy_generate_encrypted_keys_list.assert_called_once()
    spy_upload_many.assert_called_once()


def test_encrypt_cert_content(mocker: MockerFixture, mock_certificate_bytes: bytes,
                              mock_private_key: rsa.RSAPrivateKey,
                              mock_padding: padding.AsymmetricPadding,
                              mock_container_key_bytes: bytes):
    """
    To test the encryption process:
    1- Run it
    2- Also decrypt it back with the generated private key

    Assert that:
    1- Encrypted container key is larger (added padding!) than the original container key
        - This also ensures it it different than the original key
    2- Decrypted key is equal to the original container key

    """
    encrypted_key = GrantAccess._encrypt_public_key_from_certificate(
        certificate_bytes=mock_certificate_bytes,
        container_key_bytes=mock_container_key_bytes,
        padding=mock_padding
    )
    decrypted_key = mock_private_key.decrypt(
        ciphertext=encrypted_key,
        padding=mock_padding
    )

    assert len(encrypted_key) > len(mock_container_key_bytes)
    assert decrypted_key == mock_container_key_bytes
