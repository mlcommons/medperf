import pytest
from medperf.commands import utils as utils_module

PATCH_UTILS = "medperf.commands.utils.{}"


class DummyConfig:
    def __init__(self):
        self.active_profile = {
            "certificate_authority_id": 1,
            "certificate_authority_fingerprint": "abc",
        }


@pytest.fixture
def profile_mocks(mocker):
    dummy_config = DummyConfig()
    mocker.patch(PATCH_UTILS.format("read_config"), return_value=dummy_config)
    spy_write = mocker.patch(PATCH_UTILS.format("write_config"))
    spy_verify = mocker.patch(PATCH_UTILS.format("verify_certificate_authority_by_id"))
    return dummy_config, spy_write, spy_verify


def test_set_profile_args_updates_and_writes_config(profile_mocks):
    dummy_config, spy_write, spy_verify = profile_mocks

    # Act: update CA id
    new_args = {"certificate_authority_id": 2}
    utils_module.set_profile_args(new_args)

    # Assert
    assert dummy_config.active_profile["certificate_authority_id"] == 2
    spy_write.assert_called_once_with(dummy_config)
    spy_verify.assert_called_once_with(2, "abc")


def test_set_profile_args_updates_fingerprint(profile_mocks):
    dummy_config, spy_write, spy_verify = profile_mocks

    # Act: update fingerprint
    new_args = {"certificate_authority_fingerprint": "def"}
    utils_module.set_profile_args(new_args)

    # Assert
    assert dummy_config.active_profile["certificate_authority_fingerprint"] == "def"
    spy_write.assert_called_once_with(dummy_config)
    spy_verify.assert_called_once_with(1, "def")


def test_set_profile_args_updates_both(profile_mocks):
    dummy_config, spy_write, spy_verify = profile_mocks

    # Act: update fingerprint
    new_args = {
        "certificate_authority_fingerprint": "def",
        "certificate_authority_id": 2,
    }
    utils_module.set_profile_args(new_args)

    # Assert
    assert dummy_config.active_profile["certificate_authority_fingerprint"] == "def"
    assert dummy_config.active_profile["certificate_authority_id"] == 2
    spy_write.assert_called_once_with(dummy_config)
    spy_verify.assert_called_once_with(2, "def")


def test_set_profile_args_no_verification_if_no_change(profile_mocks):
    dummy_config, spy_write, spy_verify = profile_mocks

    # Act: update irrelevant field
    new_args = {"some_other_field": "value"}
    utils_module.set_profile_args(new_args)

    # Assert
    assert dummy_config.active_profile.get("some_other_field") == "value"
    spy_write.assert_called_once_with(dummy_config)
    spy_verify.assert_not_called()


def test_set_profile_args_no_verification_if_no_change2(profile_mocks):
    dummy_config, spy_write, spy_verify = profile_mocks

    # Act: update irrelevant field
    new_args = {
        "certificate_authority_id": 1,
        "certificate_authority_fingerprint": "abc",
    }
    utils_module.set_profile_args(new_args)

    # Assert
    spy_write.assert_called_once_with(dummy_config)
    spy_verify.assert_not_called()
