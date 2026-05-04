from copy import deepcopy
import importlib
import threading
import socket
import time

import pytest
from selenium import webdriver
from _pytest.assertion import truncate

from medperf import config
from medperf.comms.rest import REST
from medperf.init import initialize
from medperf.ui.interface import UI
from medperf.web_ui.app import run, web_app
from medperf.web_ui.tests import config as tests_config

truncate.DEFAULT_MAX_LINES = 9999
truncate.DEFAULT_MAX_CHARS = 9999

HOST = tests_config.HOST
PORT = tests_config.WEBUI_PORT


def _start_server():
    run(port=PORT)


@pytest.fixture(scope="session", autouse=True)
def package_init():
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
def webui_server(package_init):
    thread = threading.Thread(target=_start_server, daemon=True)
    thread.start()

    for _ in range(50):
        try:
            with socket.create_connection((HOST, PORT), timeout=1):
                break
        except OSError:
            time.sleep(0.2)
    else:
        raise RuntimeError("WebUI did not start")

    yield f"http://{HOST}:{PORT}"


@pytest.fixture
def ui(mocker, package_init):
    ui = mocker.create_autospec(spec=UI, spec_set=False)
    config.ui = ui
    ui.get_all_notifications = mocker.Mock(return_value=[])
    ui.get_unread_notifications_count = mocker.Mock(return_value=0)
    ui.get_all_global_events = mocker.Mock(return_value=[])
    ui.reset_global_waiting_events = mocker.Mock()
    ui.get_notification = mocker.Mock(return_value=None)
    ui.get_global_event = mocker.Mock(return_value=None)
    return ui


@pytest.fixture
def comms(mocker, package_init):
    comms = mocker.create_autospec(spec=REST)
    config.comms = comms
    return comms


@pytest.fixture
def auth(mocker, package_init):
    auth = mocker.Mock()
    config.auth = auth
    return auth


@pytest.fixture
def driver_noauth():
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument("--headless=true")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=opts)
    driver.maximize_window()
    driver.get(f"http://{HOST}:{PORT}")
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def sec_token(webui_server):
    from medperf.web_ui.auth import security_token

    return security_token


@pytest.fixture(scope="session")
def driver(sec_token):
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument("--headless=true")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=opts)
    driver.maximize_window()
    driver.get(f"http://{HOST}:{PORT}/security_check?token={sec_token}")

    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def reset_app():
    web_app.state.task_running = False
    web_app.state.task.running = False
    web_app.state.task.name = ""
    web_app.state.task.formData = {}
