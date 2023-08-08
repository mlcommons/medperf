from medperf.comms.auth.interface import Auth
import pytest
import requests
import builtins
import os

from medperf import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms


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


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    config.ui = ui
    return ui


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    config.comms = comms
    return comms


@pytest.fixture
def auth(mocker):
    auth = mocker.create_autospec(spec=Auth)
    config.auth = auth
    return auth
