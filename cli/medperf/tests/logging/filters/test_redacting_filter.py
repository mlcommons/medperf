import pytest
import logging

from medperf import config
from medperf.utils import setup_logging, storage_path


@pytest.fixture
def setup(fs):
    log_file = storage_path(config.log_file)
    fs.create_file(log_file)
    setup_logging("DEBUG")
    return log_file


@pytest.mark.parametrize(
    "text,exp_output",
    [
        ("password: 123", "password: [redacted]"),
        ("password='test", "password=[redacted]"),
        ('token="2872547"', "token=[redacted]"),
        ("\{'token': '279438'\}", "\{'token': [redacted]\}"),
    ],
)
def test_logging_filters_sensitive_data(text, exp_output, setup):
    # Arrange
    log_file = setup

    # Act
    logging.debug(text)

    # Assert
    with open(log_file) as f:
        data = f.read()

    assert exp_output in data
