import pytest
import requests
import builtins
import os


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise Exception("There was an attempt at executing a get request")

    def stunted_post():
        raise Exception("There was an attempt at executing a post request")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: stunted_post())


@pytest.fixture(autouse=True)
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

    monkeypatch.setattr(os, "walk", lambda *args, **kwargs: stunted_walk())
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: stunted_remove())
    monkeypatch.setattr(os, "chmod", lambda *args, **kwargs: stunted_chmod())
    monkeypatch.setattr(os, "mkdir", lambda *args, **kwargs: stunted_mkdir())
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: stunted_mkdir())
    monkeypatch.setattr(os.path, "isdir", lambda *args, **kwargs: stunted_isdir())
    # monkeypatch.setattr(os.path, "abspath", lambda *args, **kwargs: stunted_abspath())
    # monkeypatch.setattr(os.path, "exists", lambda *args, **kwargs: stunted_exists())
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: stunted_open())
