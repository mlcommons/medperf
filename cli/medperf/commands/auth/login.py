import os
import stat
import configparser

from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms


class Login:
    @staticmethod
    def run(comms: Comms, ui: UI, username: str = None, password: str = None):
        """Login to the medperf server. Must be done only once.
        """
        cred_path = os.path.join(config.storage, config.credentials_path)
        user = username if username else ui.prompt("username: ")
        pwd = password if password else ui.hidden_prompt("password: ")
        comms.login(ui, user, pwd)
        token = comms.token

        creds = configparser.ConfigParser()
        profile = config.profile
        if os.path.exists(cred_path):
            creds.read(cred_path)
            os.chmod(cred_path, stat.S_IWRITE)

        creds[profile] = {"token": token}
        with open(cred_path, "w") as f:
            creds.write(f)

        os.chmod(cred_path, stat.S_IREAD)
