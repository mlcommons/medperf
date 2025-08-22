from __future__ import annotations
import base64
import pytest
from medperf.entities.certificate import Certificate
from medperf.exceptions import MedperfException

PATCH_ASSOC = "medperf.entities.certificate.{}"


@pytest.fixture
def bytes_content() -> bytes:
    return b'some_content'


@pytest.fixture
def b64_content(bytes_content: bytes) -> str:
    return base64.b64encode(bytes_content).decode("utf-8")


def test_generates_b64_content_from_bytes_content(bytes_content: bytes, b64_content: str):
    cert = Certificate(name='TestCert', id=1, owner=None, ca_id=1,
                       for_test=True, certificate_content=bytes_content)

    assert cert.certificate_content_base64 == b64_content


def test_generates_bytes_content_from_b64_content(bytes_content: bytes, b64_content: str):
    cert = Certificate(name='TestCert', id=1, owner=None, ca_id=1,
                       for_test=True, certificate_content_base64=b64_content)
    assert cert.certificate_content == bytes_content


def test_accepts_both_bytes_and_b64_if_equal(bytes_content, b64_content):
    cert = Certificate(name='TestCert', id=1, owner=None, ca_id=1,
                       for_test=True, certificate_content_base64=b64_content,
                       certificate_content=bytes_content)
    assert cert.certificate_content_base64 == b64_content
    assert cert.certificate_content == bytes_content
    assert base64.b64encode(cert.certificate_content).decode('utf-8') == cert.certificate_content_base64
    assert base64.b64decode(cert.certificate_content_base64.encode('utf-8')) == cert.certificate_content


def test_raises_error_if_content_mismatch():
    with pytest.raises(MedperfException):
        Certificate(name='TestCert', id=1, owner=None, ca_id=1,
                    for_test=True, certificate_content=b'some_content',
                    certificate_content_base64='content that does not match')


def test_raises_error_if_no_contents():
    with pytest.raises(MedperfException):
        Certificate(name='TestCert', id=1, owner=None, ca_id=1,
                    for_test=True)
