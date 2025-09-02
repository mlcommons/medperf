from __future__ import annotations
import pytest
from pytest_mock import MockerFixture
from typing import TYPE_CHECKING
from medperf.entities.ca import CA
from medperf import config
from medperf.entities.certificate import Certificate
from medperf.commands.certificate.submit import SubmitCertificate
import os
from medperf.exceptions import InvalidArgumentError

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem

PATCH_ASSOC = "medperf.commands.certificate.submit.{}"


@pytest.fixture(autouse=True)
def setup_certificate_submit_tests(mocker: MockerFixture,
                                   mock_ca: CA, mock_pki_assets_path: str,
                                   mock_certificate_file: str,
                                   fs: FakeFilesystem):
    mocker.patch.object(CA, 'get', return_value=mock_ca)
    fs.create_dir(mock_pki_assets_path)
    mocker.patch.object(Certificate, 'user_email', 'johndoe@test.com')
    fs.create_file(mock_certificate_file, contents=b'testcert')
    mocker.patch(PATCH_ASSOC.format('get_medperf_user_data'),
                 return_value={'email': 'johndoe@test.com'})
    mocker.patch(PATCH_ASSOC.format("get_pki_assets_path"),
                 return_value=mock_pki_assets_path)


@pytest.fixture
def mock_certificate() -> Certificate:
    mock_cert = Certificate(id=1,
                            name='TestCert',
                            owner=None,
                            for_test=True,
                            certificate_content=b'some_content',
                            ca=10)
    return mock_cert


@pytest.fixture
def mock_ca() -> CA:
    ca = CA(id=10, name='TestCA', owner=None, for_test=True,
            server_mlcube=1, client_mlcube=1, ca_mlcube=1, ca_dict={},
            config={'address': 'www.test.com', 'port': '1234', 'fingerprint': '',
                    'client_provisioner': '', 'server_provisioner': ''})
    return ca


@pytest.fixture
def mock_pki_assets_path() -> str:
    fake_pki_assets = '/path/to/fake/pki/assets'
    return fake_pki_assets


@pytest.fixture
def mock_certificate_file(mock_pki_assets_path: str) -> str:
    fake_cert = os.path.join(mock_pki_assets_path, config.certificate_file)
    return fake_cert


def test_submit_prepares_tmp_path_for_cleanup(mock_ca: CA):
    # Act
    submission = SubmitCertificate(ca_id=mock_ca.id, name='TestSubmit')

    # Assert
    assert submission.certificate.path in config.tmp_paths


@pytest.mark.parametrize('model_id, ca_id, training_exp_id',
                         [
                             (1, None, None),
                             (None, 1, None),
                             (None, None, 1)
                         ])
def test_run_runs_expected_flow(mocker: MockerFixture,
                                mock_ca: CA, mock_certificate: Certificate,
                                model_id: int, ca_id: int, training_exp_id: int,
                                ):
    # Arrange
    spy_upload = mocker.patch.object(Certificate, 'upload', return_value=mock_certificate.todict())
    spy_write = mocker.patch.object(Certificate, 'write')
    spy_verify_with_ca = mocker.patch.object(Certificate, 'verify_with_ca')
    spy_get_ca = mocker.patch(PATCH_ASSOC.format('get_ca_from_id_model_or_training_exp'),
                              return_value=mock_ca)
    args_dict = {'ca_id': ca_id, 'model_id': model_id, 'training_exp_id': training_exp_id}
    # Act
    SubmitCertificate.run(name='TestSubmit', approved=True, **args_dict)

    # Assert
    spy_write.assert_called_once()
    spy_upload.assert_called_once()
    spy_verify_with_ca.assert_called_once()
    spy_get_ca.assert_called_once_with(**args_dict)


@pytest.mark.parametrize('model_id, ca_id, training_exp_id',
                         [
                             (1, 1, None),
                             (2, None, 2),
                             (None, 3, 3),
                             (4, 4, 4)
                         ])
def test_fails_more_than_one_id_provided(mocker: MockerFixture,
                                         mock_certificate: Certificate,
                                         model_id: int, ca_id: int, training_exp_id: int
                                         ):
    # Arrange
    spy_upload = mocker.patch.object(Certificate, 'upload', return_value=mock_certificate.todict())
    spy_write = mocker.patch.object(Certificate, 'write')
    spy_verify_with_ca = mocker.patch.object(Certificate, 'verify_with_ca')
    args_dict = {'ca_id': ca_id, 'model_id': model_id, 'training_exp_id': training_exp_id}
    # Act
    with pytest.raises(InvalidArgumentError):
        SubmitCertificate.run(name='TestSubmit', approved=True, **args_dict)

    # Assert
    spy_write.assert_not_called()
    spy_upload.assert_not_called()
    spy_verify_with_ca.assert_not_called()


@pytest.mark.parametrize('model_id, ca_id, training_exp_id',
                         [
                             (1, None, None),
                             (None, 1, None),
                             (None, None, 1),
                             (1, 1, None),
                             (2, None, 2),
                             (None, 3, 3),
                             (4, 4, 4)
                         ])
def test_cancels_with_negative_prompt_answer(mocker: MockerFixture,
                                             mock_ca: CA, mock_certificate: Certificate,
                                             model_id: int, ca_id: int, training_exp_id: int,
                                             ):
    # Arrange
    spy_upload = mocker.patch.object(Certificate, 'upload', return_value=mock_certificate.todict())
    spy_write = mocker.patch.object(Certificate, 'write')
    spy_verify_with_ca = mocker.patch.object(Certificate, 'verify_with_ca')
    spy_get_ca = mocker.patch(PATCH_ASSOC.format('get_ca_from_id_model_or_training_exp'),
                              return_value=mock_ca)
    spy_prompt = mocker.patch(PATCH_ASSOC.format('approval_prompt'), return_value=False)
    args_dict = {'ca_id': ca_id, 'model_id': model_id, 'training_exp_id': training_exp_id}
    # Act
    SubmitCertificate.run(name='TestSubmit', approved=False, **args_dict)

    # Assert
    spy_write.assert_not_called()
    spy_upload.assert_not_called()
    spy_verify_with_ca.assert_not_called()
    spy_get_ca.assert_not_called()
    spy_prompt.assert_called_once
