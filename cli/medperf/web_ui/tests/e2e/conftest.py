import pytest
import yaml

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from medperf import config


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
