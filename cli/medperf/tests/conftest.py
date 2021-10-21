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
    def stuned_walk():
        raise Exception("There was an attempt at walking through the filesystem")

    def stuned_open():
        raise Exception("There was an attempt at opening a file for IO")

    def stuned_exists():
        raise Exception("There was an attempt at checking the existence of a fs object")

    def stuned_remove():
        raise Exception("There was an attempt at removing a fs object")

    def stuned_chmod():
        raise Exception("There was an attempt at modifying a fs object permissions")

    def stuned_isdir():
        raise Exception(
            "There was an attempt at checking if a fs object is a directory"
        )

    def stuned_abspath():
        raise Exception("There was an attempt at converting a path to absolute")

    def stuned_mkdir():
        raise Exception("There was an attempt at creating a directory")

    monkeypatch.setattr(os, "walk", lambda *args, **kwargs: stuned_walk())
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: stuned_remove())
    monkeypatch.setattr(os, "chmod", lambda *args, **kwargs: stuned_chmod())
    monkeypatch.setattr(os, "mkdir", lambda *args, **kwargs: stuned_mkdir())
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: stuned_mkdir())
    monkeypatch.setattr(os.path, "isdir", lambda *args, **kwargs: stuned_isdir())
    # monkeypatch.setattr(os.path, "abspath", lambda *args, **kwargs: stuned_abspath())
    # monkeypatch.setattr(os.path, "exists", lambda *args, **kwargs: stuned_exists())
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: stuned_open())
