import yaml


class ConfigManager:
    def __init__(self):
        self.active_profile_name = None
        self.profiles = {}

    @property
    def active_profile(self):
        return self.profiles[self.active_profile_name]

    def activate(self, profile_name):
        self.active_profile_name = profile_name

    def is_profile_active(self, profile_name):
        return self.active_profile_name == profile_name

    def read(self, path):
        with open(path) as f:
            data = yaml.safe_load(f)
        self.active_profile_name = data["active_profile_name"]
        self.profiles = data["profiles"]

    def write(self, path):
        data = {
            "active_profile_name": self.active_profile_name,
            "profiles": self.profiles,
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
