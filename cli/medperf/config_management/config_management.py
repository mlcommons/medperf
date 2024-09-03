import os
from typing import Optional, Dict, Any

import yaml
from medperf import settings
from medperf.comms.factory import create_comms
from medperf.comms.interface import Comms
from medperf.ui.factory import create_ui
from medperf.ui.interface import UI


class ConfigManager:
    def __init__(self):
        self.active_profile_name = None
        self.profiles = {}
        self.storage = {}

        self._fields_to_override: Optional[Dict[str, Any]] = None
        self._profile_to_override: Optional[str] = None

        self.ui: UI = None
        self.comms: Comms = None

    def keep_overridden_fields(self, profile_name: Optional[str] = None, **kwargs):
        """User might override some fields temporarily through the CLI params. We'd like to
        use these overridden fields every time config is read, but we don't want to save them
        to the yaml file. This method allows us to keep these fields in memory, and apply them.
        If profile name is given, updates should be applied to that profile only.
        """
        self._fields_to_override = kwargs
        self._profile_to_override = profile_name

    def _override_fields(self) -> None:
        if (self._profile_to_override is not None
                and self._profile_to_override != self.active_profile_name):
            return

        if self._fields_to_override:
            self.profiles[self.active_profile_name] = {**self.active_profile, **self._fields_to_override}

    @property
    def active_profile(self):
        return self.profiles[self.active_profile_name]

    def _recreate_ui(self):
        ui_type = self.active_profile.get("ui") or settings.default_ui
        self.ui = create_ui(ui_type)

    def _recreate_comms(self):
        comms_type = self.active_profile.get("comms") or settings.default_comms
        server = self.active_profile.get("server") or settings.server
        if "certificate" in self.active_profile:
            cert = self.active_profile.get("certificate")
        else:
            cert = settings.certificate
        self.comms = create_comms(comms_type, server, cert)

    def _recreate_auth(self):
        pass

    def activate(self, profile_name):
        self.active_profile_name = profile_name
        self._override_fields()
        # Setup UI, COMMS
        self._recreate_ui()
        self._recreate_auth()
        self._recreate_comms()

    def is_profile_active(self, profile_name):
        return self.active_profile_name == profile_name

    def _read(self, path):
        with open(path) as f:
            data = yaml.safe_load(f)
        self.profiles = data["profiles"]
        self.storage = data["storage"]

        self.activate(data["active_profile_name"])

    def write(self, path):
        data = {
            "active_profile_name": self.active_profile_name,
            "profiles": self.profiles,
            "storage": self.storage,
        }
        with open(path, "w") as f:
            yaml.dump(data, f)

    def __getitem__(self, key):
        return self.profiles[key]

    def __setitem__(self, key, val):
        self.profiles[key] = val

    def __delitem__(self, key):
        del self.profiles[key]

    def __iter__(self):
        return iter(self.profiles)

    def read_config(self):
        config_path = settings.config_path
        self._read(config_path)
        return self

    def write_config(self):
        config_path = settings.config_path
        self.write(config_path)


config = ConfigManager()
