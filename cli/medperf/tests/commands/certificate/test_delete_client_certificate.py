import shutil
import pytest
from medperf.commands.certificate.delete_client_certificate import DeleteCertificate
from medperf.tests.mocks.certificate import TestCertificate
from medperf.exceptions import CleanExit
from medperf import config

PATCH_DELETE = "medperf.commands.certificate.delete_client_certificate.{}"


@pytest.fixture
def delete_fixture(mocker, fs):
    email = "alice@example.com"
    mocker.patch(
        PATCH_DELETE.format("get_medperf_user_data"), return_value={"email": email}
    )
    mocker.patch(PATCH_DELETE.format("approval_prompt"), return_value=True)
    folder = f"/pki/{email}/{config.certificate_authority_id}"
    fs.create_dir(folder)
    mocker.patch(PATCH_DELETE.format("get_pki_assets_path"), return_value=folder)
    mocker.patch(PATCH_DELETE.format("remove_path"))
    return folder


def test_run_raises_if_not_approved(mocker, delete_fixture):
    # Arrange
    mocker.patch(PATCH_DELETE.format("approval_prompt"), return_value=False)

    # Act & Assert
    with pytest.raises(CleanExit):
        DeleteCertificate.run(approved=False)


def test_run_deletes_local_folder_and_invalidates_remote_cert(mocker, delete_fixture):
    # Arrange
    cert = TestCertificate(id=123)
    mocker.patch(
        PATCH_DELETE.format("Certificate.get_user_certificate"), return_value=cert
    )
    remove_path_spy = mocker.patch(PATCH_DELETE.format("remove_path"))
    update_spy = mocker.patch.object(config.comms, "update_certificate")

    # Act
    DeleteCertificate.run(approved=True)

    # Assert
    remove_path_spy.assert_called_once_with(delete_fixture, sensitive=True)
    update_spy.assert_called_once_with(123, {"is_valid": False})


def test_run_deletes_local_folder_only_if_no_remote_cert(mocker, delete_fixture):
    # Arrange
    mocker.patch(PATCH_DELETE.format("approval_prompt"), return_value=True)
    mocker.patch(
        PATCH_DELETE.format("Certificate.get_user_certificate"), return_value=None
    )
    remove_path_spy = mocker.patch(PATCH_DELETE.format("remove_path"))
    update_spy = mocker.patch.object(config.comms, "update_certificate")

    # Act
    DeleteCertificate.run(approved=True)

    # Assert
    remove_path_spy.assert_called_once_with(delete_fixture, sensitive=True)
    update_spy.assert_not_called()


def test_run_deletes_local_folder_anyway(mocker, delete_fixture):
    # Arrange
    shutil.rmtree(delete_fixture)
    mocker.patch(PATCH_DELETE.format("approval_prompt"), return_value=True)
    mocker.patch(
        PATCH_DELETE.format("Certificate.get_user_certificate"), return_value=None
    )
    remove_path_spy = mocker.patch(PATCH_DELETE.format("remove_path"))

    # Act
    DeleteCertificate.run(approved=True)

    # Assert
    remove_path_spy.assert_called_once_with(delete_fixture, sensitive=True)
