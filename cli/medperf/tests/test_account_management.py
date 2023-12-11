import pytest

import medperf.config as config
from medperf.exceptions import MedperfException
from medperf import account_management

PATCH_ACC = "medperf.account_management.account_management.{}"


class MockConfig:
    def __init__(self, **kwargs):
        self.active_profile = kwargs


@pytest.fixture
def mock_config(mocker, request):
    try:
        param = request.param
    except AttributeError:
        param = {}
    config_p = MockConfig(**param)
    mocker.patch(PATCH_ACC.format("read_config"), return_value=config_p)
    mocker.patch(PATCH_ACC.format("write_config"))
    return config_p


def test_get_medperf_user_data_fail_for_not_logged_in_user(mock_config):
    with pytest.raises(MedperfException):
        account_management.get_medperf_user_data()


@pytest.mark.parametrize(
    "mock_config", [{config.credentials_keyword: {}}], indirect=True
)
def test_get_medperf_user_data_gets_data_from_comms(mocker, mock_config, comms):
    # Arrange
    medperf_user = "medperf_user"
    mocker.patch.object(comms, "get_current_user", return_value=medperf_user)

    # Act
    account_management.get_medperf_user_data()

    # Assert
    assert (
        mock_config.active_profile[config.credentials_keyword]["medperf_user"]
        == medperf_user
    )


@pytest.mark.parametrize(
    "mock_config",
    [{config.credentials_keyword: {"medperf_user": "some data"}}],
    indirect=True,
)
def test_get_medperf_user_data_gets_data_from_cache(mocker, mock_config, comms):
    # Arrange
    spy = mocker.patch.object(comms, "get_current_user")

    # Act
    account_management.get_medperf_user_data()

    # Assert
    spy.assert_not_called()
