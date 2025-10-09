import importlib
import pytest
import yaml
from copy import deepcopy

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from medperf.config_management import read_config, write_config
from medperf.init import initialize
from medperf import config

TEST_PROFILE = "local"


@pytest.fixture(scope="session", autouse=True)
def package_init():
    # TODO: this might not be enough. Fixtures that don't depend on
    #       ui, auth, or comms may still run before this fixture
    #       all of this should hacky test setup be changed anyway
    orig_config_as_dict = {}
    try:
        orig_config = importlib.reload(config)
    except ImportError:
        orig_config = importlib.import_module("medperf.config", "medperf")
    for attr in dir(orig_config):
        if not attr.startswith("__"):
            orig_config_as_dict[attr] = deepcopy(getattr(orig_config, attr))
    initialize(for_webui=True)
    yield
    for attr in orig_config_as_dict:
        setattr(config, attr, orig_config_as_dict[attr])


@pytest.fixture(scope="session", autouse=True)
def activate_local_profile():
    config_p = read_config()
    if config_p.active_profile_name != TEST_PROFILE:
        config_p.activate(TEST_PROFILE)
        write_config(config_p)


@pytest.fixture(scope="session", autouse=True)
def driver():
    options = Options()
    options.add_argument("--headless=true")  # run without opening a real window
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def sec_token():
    with open(config.webui_host_props) as f:
        data = yaml.safe_load(f)
    return data.get("security_token", "")
