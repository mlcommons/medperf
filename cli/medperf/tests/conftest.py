import pytest
import requests
import builtins
import os
from copy import deepcopy
from medperf import config
from medperf.ui.interface import UI
from medperf.comms.rest import REST
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
def package_init(fs):
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
    initialize()
    yield
    for attr in orig_config_as_dict:
        setattr(config, attr, orig_config_as_dict[attr])


@pytest.fixture
def ui(mocker, package_init):
    ui = mocker.create_autospec(spec=UI)
    config.ui = ui
    return ui


@pytest.fixture
def comms(mocker, package_init):
    comms = mocker.create_autospec(spec=REST)
    config.comms = comms
    return comms


@pytest.fixture
def auth(mocker, package_init):
    auth = mocker.create_autospec(spec=Auth)
    config.auth = auth
    return auth
