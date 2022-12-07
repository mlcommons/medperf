import os
import stat
import configparser

import medperf.config as config


class Login:
    @staticmethod
    def run(username: str = None, password: str = None):
        """Login to the medperf server. Must be done only once.
        """
        comms = config.comms
        ui = config.ui
        cred_path = os.path.join(config.storage, config.credentials_path)
        user = username if username else ui.prompt("username: ")
        pwd = password if password else ui.hidden_prompt("password: ")
        comms.login(user, pwd)
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
