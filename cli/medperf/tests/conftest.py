import pytest
import requests
import builtins
import os
from copy import deepcopy
from medperf import settings
from medperf.config_management import config_management
from medperf.config_management import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.comms.auth.interface import Auth
from medperf.init import initialize
import importlib


# from copy import deepcopy


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise Exception("There was an attempt at executing a get request")

    def stunted_post():
        raise Exception("There was an attempt at executing a post request")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: stunted_post())


@pytest.fixture()
def disable_fs_IO_operations(monkeypatch):
    def stunted_walk():
        raise Exception("There was an attempt at walking through the filesystem")

    def stunted_open():
        raise Exception("There was an attempt at opening a file for IO")

    def stunted_exists():
        raise Exception("There was an attempt at checking the existence of a fs object")

    def stunted_remove():
        raise Exception("There was an attempt at removing a fs object")

    def stunted_chmod():
        raise Exception("There was an attempt at modifying a fs object permissions")

    def stunted_isdir():
        raise Exception(
            "There was an attempt at checking if a fs object is a directory"
        )

    def stunted_abspath():
        raise Exception("There was an attempt at converting a path to absolute")

    def stunted_mkdir():
        raise Exception("There was an attempt at creating a directory")

    def stunted_listdir():
        raise Exception("There was an attempt at listing a directory")

    monkeypatch.setattr(os, "walk", lambda *args, **kwargs: stunted_walk())
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: stunted_remove())
    monkeypatch.setattr(os, "chmod", lambda *args, **kwargs: stunted_chmod())
    monkeypatch.setattr(os, "mkdir", lambda *args, **kwargs: stunted_mkdir())
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: stunted_mkdir())
    monkeypatch.setattr(os, "listdir", lambda *args, **kwargs: stunted_listdir())
    monkeypatch.setattr(os.path, "isdir", lambda *args, **kwargs: stunted_isdir())
    # monkeypatch.setattr(os.path, "abspath", lambda *args, **kwargs: stunted_abspath())
    # monkeypatch.setattr(os.path, "exists", lambda *args, **kwargs: stunted_exists())
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: stunted_open())


@pytest.fixture(autouse=True)
def package_init(fs, monkeypatch):
    # TODO: this might not be enough. Fixtures that don't depend on
    #       ui, auth, or comms may still run before this fixture
    #       all of this should hacky test setup be changed anyway
    orig_settings_as_dict = {}
    try:
        orig_settings = importlib.reload(settings)
    except ImportError:
        orig_settings = importlib.import_module("medperf.settings", "medperf")

    try:
        config_mgmt = importlib.reload(config_management)
    except ImportError:
        config_mgmt = importlib.import_module("medperf.config_management.config_management",
                                              "medperf.config_management")
    monkeypatch.setattr('medperf.config_management.config', config_mgmt.config)

    for attr in dir(orig_settings):
        if not attr.startswith("__"):
            orig_settings_as_dict[attr] = deepcopy(getattr(orig_settings, attr))
    initialize()
    yield
    for attr in orig_settings_as_dict:
        setattr(settings, attr, orig_settings_as_dict[attr])


@pytest.fixture
def ui(mocker, package_init):
    ui = mocker.create_autospec(spec=UI)
    config.ui = ui
    return ui


@pytest.fixture
def comms(mocker, package_init):
    comms = mocker.create_autospec(spec=Comms)
    config.comms = comms
    return comms


@pytest.fixture
def auth(mocker, package_init):
    auth = mocker.create_autospec(spec=Auth)
    settings.auth = auth
    return auth


@pytest.fixture
def fs(fs):
    fs.add_real_file(
        settings.local_tokens_path,
        target_path=settings.local_tokens_path
    )
    yield fs
