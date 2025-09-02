from __future__ import annotations
import base64
import pytest
from medperf.entities.encrypted_container_key import EncryptedContainerKey
from medperf.exceptions import MedperfException, DecryptionError
from typing import TYPE_CHECKING
from medperf.entities.cube import Cube
from medperf.entities.ca import CA
from pathlib import Path
from medperf import config
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

PATCH_ASSOC = 'medperf.entities.encrypted_container_key.{}'


@pytest.fixture
def mock_bytes_key() -> bytes:
    return b'some_key'


@pytest.fixture
def mock_b64_key(mock_bytes_key: bytes) -> str:
    return base64.b64encode(mock_bytes_key).decode("utf-8")


@pytest.fixture
def private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


@pytest.fixture
def unencrypted_container_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture
def padding_obj() -> padding.AsymmetricPadding:
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )


@pytest.fixture
def encrypted_container_key(unencrypted_container_key: bytes,
                            private_key: rsa.RSAPrivateKey,
                            padding_obj: padding.AsymmetricPadding):
    public_key = private_key.public_key()

    encrypted_cont_key = public_key.encrypt(plaintext=unencrypted_container_key,
                                            padding=padding_obj)
    return encrypted_cont_key


def _arrange_for_decryption_tests(mocker: MockerFixture, fs: FakeFilesystem,
                                  encrypted_container_key: bytes,
                                  padding_obj: padding.AsymmetricPadding,
                                  private_key: rsa.RSAPrivateKey):
    # Arrange
    encrypted_key_obj = EncryptedContainerKey(name='TestCert', id=1, owner=None,
                                              for_test=True,encrypted_key=encrypted_container_key,
                                              certificate=1, model_container=1,
                                              padding=padding_obj)
    ca = mocker.create_autospec(CA)
    ca.name = 'TestDecryptCA'
    ca.id = 1
    container = mocker.create_autospec(Cube)
    container.name = 'TestDecryptContainer'
    container.id = 1

    mock_pki_assets_path = Path(f'/path/to/pki/assets/{ca.id}')
    mock_get_user_data = mocker.patch(PATCH_ASSOC.format('get_medperf_user_data'),
                                      return_value={'email': 'testrun@test.com'})
    mock_get_pki_assets_path = mocker.patch(PATCH_ASSOC.format('get_pki_assets_path'),
                                            return_value=str(mock_pki_assets_path))
    mock_private_key_path = mock_pki_assets_path / config.private_key_file

    private_key_bytes = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                                  format=serialization.PrivateFormat.TraditionalOpenSSL,
                                                  encryption_algorithm=serialization.NoEncryption())
    fs.create_dir(mock_pki_assets_path)
    fs.create_file(mock_private_key_path, contents=private_key_bytes)
    return encrypted_key_obj, ca, container, mock_get_user_data, mock_get_pki_assets_path


def test_generates_b64_key_from_bytes_key(mock_bytes_key: bytes, mock_b64_key: str):
    encrypted_key = EncryptedContainerKey(name='TestCert', id=1, owner=None, certificate=1,
                                          for_test=True, encrypted_key=mock_bytes_key,
                                          model_container=1)

    assert encrypted_key.encrypted_key_base64 == mock_b64_key


def test_generates_bytes_key_from_b64_key(mock_bytes_key: bytes, mock_b64_key: str):
    encrypted_key = EncryptedContainerKey(name='TestCert', id=1, owner=None, certificate=1,
                                          for_test=True, encrypted_key_base64=mock_b64_key,
                                          model_container=1)
    assert encrypted_key.encrypted_key == mock_bytes_key


def test_accepts_both_bytes_and_b64_if_equal(mock_bytes_key, mock_b64_key):
    encrypted_key = EncryptedContainerKey(name='TestCert', id=1, owner=None, for_test=True,
                                          encrypted_key_base64=mock_b64_key,
                                          encrypted_key=mock_bytes_key,
                                          certificate=1, model_container=1)
    assert encrypted_key.encrypted_key_base64 == mock_b64_key
    assert encrypted_key.encrypted_key == mock_bytes_key
    assert base64.b64encode(encrypted_key.encrypted_key).decode('utf-8') == encrypted_key.encrypted_key_base64
    assert base64.b64decode(encrypted_key.encrypted_key_base64.encode('utf-8')) == encrypted_key.encrypted_key


def test_raises_error_if_key_mismatch(mock_bytes_key):
    with pytest.raises(MedperfException):
        EncryptedContainerKey(name='TestCert', id=1, owner=None, for_test=True,
                              encrypted_key_base64='unmatching key',
                              encrypted_key=mock_bytes_key,
                              certificate=1, model_container=1)


def test_raises_error_if_no_keys():
    with pytest.raises(MedperfException):
        EncryptedContainerKey(name='TestCert', id=1, owner=None, for_test=True,
                              certificate=1, model_container=1)


def test_decrypt(unencrypted_container_key: bytes, private_key: rsa.RSAPrivateKey,
                 padding_obj: padding.AsymmetricPadding, encrypted_container_key: bytes,
                 fs: FakeFilesystem, mocker: MockerFixture):
    # Arrange
    args_tuple = _arrange_for_decryption_tests(mocker=mocker, fs=fs,
                                               encrypted_container_key=encrypted_container_key,
                                               padding_obj=padding_obj, private_key=private_key)
    encrypted_key_obj, ca, container, mock_get_user_data, mock_get_pki_assets_path = args_tuple

    # Act
    decrypted_container_key = encrypted_key_obj.decrypt_key(ca=ca, container=container)

    # Assert
    assert decrypted_container_key != encrypted_container_key
    assert decrypted_container_key == unencrypted_container_key
    assert unencrypted_container_key != encrypted_container_key
    mock_get_user_data.assert_called_once()
    mock_get_pki_assets_path.assert_called_once()


def test_decrypt_fails_wrong_key(padding_obj: padding.AsymmetricPadding, encrypted_container_key: bytes,
                                 fs: FakeFilesystem, mocker: MockerFixture):
    # Arrange
    unrelated_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    args_tuple = _arrange_for_decryption_tests(mocker=mocker, fs=fs,
                                               encrypted_container_key=encrypted_container_key,
                                               padding_obj=padding_obj, private_key=unrelated_key)
    encrypted_key_obj, ca, container, mock_get_user_data, mock_get_pki_assets_path = args_tuple

    # Act
    with pytest.raises(DecryptionError):
        encrypted_key_obj.decrypt_key(ca=ca, container=container)

    # Assert
    mock_get_user_data.assert_called_once()
    mock_get_pki_assets_path.assert_called_once()
