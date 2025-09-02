from __future__ import annotations
import base64
import pytest
from medperf.entities.certificate import Certificate
from medperf.exceptions import MedperfException
from medperf.tests.utils import generate_test_certificate
from typing import TYPE_CHECKING
from medperf.entities.ca import CA
from pathlib import Path
from medperf import config
from medperf.exceptions import InvalidCertificateError

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture


@pytest.fixture
def bytes_content() -> bytes:
    return b'some_content'


@pytest.fixture
def b64_content(bytes_content: bytes) -> str:
    return base64.b64encode(bytes_content).decode("utf-8")


def test_generates_b64_content_from_bytes_content(bytes_content: bytes, b64_content: str):
    cert = Certificate(name='TestCert', id=1, owner=None, ca=1,
                       for_test=True, certificate_content=bytes_content)

    assert cert.certificate_content_base64 == b64_content


def test_generates_bytes_content_from_b64_content(bytes_content: bytes, b64_content: str):
    cert = Certificate(name='TestCert', id=1, owner=None, ca=1,
                       for_test=True, certificate_content_base64=b64_content)
    assert cert.certificate_content == bytes_content


def test_accepts_both_bytes_and_b64_if_equal(bytes_content, b64_content):
    cert = Certificate(name='TestCert', id=1, owner=None, ca=1,
                       for_test=True, certificate_content_base64=b64_content,
                       certificate_content=bytes_content)
    assert cert.certificate_content_base64 == b64_content
    assert cert.certificate_content == bytes_content
    assert base64.b64encode(cert.certificate_content).decode('utf-8') == cert.certificate_content_base64
    assert base64.b64decode(cert.certificate_content_base64.encode('utf-8')) == cert.certificate_content


def test_raises_error_if_content_mismatch():
    with pytest.raises(MedperfException):
        Certificate(name='TestCert', id=1, owner=None, ca=1,
                    for_test=True, certificate_content=b'some_content',
                    certificate_content_base64='content that does not match')


def test_raises_error_if_no_contents():
    with pytest.raises(MedperfException):
        Certificate(name='TestCert', id=1, owner=None, ca=1,
                    for_test=True)


def test_verify_with_ca(mocker: MockerFixture, fs: FakeFilesystem):
    # Arrange
    ca_cert_info = generate_test_certificate()
    client_cert_info = generate_test_certificate(ca_cert_info)
    client_cert = Certificate(name='TestCert', id=1, owner=None, ca=1,
                              for_test=True,
                              certificate_content=client_cert_info.certificate_bytes)
    ca = mocker.create_autospec(spec=CA)
    ca.name = 'TestCA'
    ca.id = 1
    mock_pki_assets_dir = Path(f'/path/to/pki/assets/{ca.id}')
    mock_ca_cert_file = mock_pki_assets_dir / config.ca_certificate_file
    ca.pki_assets = mock_pki_assets_dir

    fs.create_dir(mock_pki_assets_dir)
    fs.create_file(mock_ca_cert_file, contents=ca_cert_info.certificate_bytes)

    # Act & Assert
    client_cert.verify_with_ca(ca=ca, validate_ca=False)


def test_does_not_verify_with_wrong_ca(mocker: MockerFixture, fs: FakeFilesystem):
    # Arrange
    ca_cert_info = generate_test_certificate()
    client_cert_info = generate_test_certificate(ca_cert_info)
    irrelevant_ca_info = generate_test_certificate()

    client_cert = Certificate(name='TestCert', id=1, owner=None, ca=1,
                              for_test=True,
                              certificate_content=client_cert_info.certificate_bytes)
    ca = mocker.create_autospec(spec=CA)
    ca.name = 'TestCA'
    ca.id = 1
    mock_pki_assets_dir = Path(f'/path/to/pki/assets/{ca.id}')
    mock_ca_cert_file = mock_pki_assets_dir / config.ca_certificate_file
    ca.pki_assets = mock_pki_assets_dir

    fs.create_dir(mock_pki_assets_dir)
    fs.create_file(mock_ca_cert_file, contents=irrelevant_ca_info.certificate_bytes)

    # Act & Assert
    with pytest.raises(InvalidCertificateError):
        client_cert.verify_with_ca(ca=ca, validate_ca=False)
