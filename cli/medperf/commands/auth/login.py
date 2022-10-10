import os
import stat

import medperf.config as config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import storage_path


class Login:
    @staticmethod
    def run(username: str = None, password: str = None, comms: Comms = config.comms, ui: UI = config.ui):
        """Login to the medperf server. Must be done only once.

        Args:
            username (str, optional): Username to login into. Defaults to prompting the user
            password (str, optional): User's password. Default to using a hidden prompt
            comms (Comms, optional): Communications instance. Defaults to config.comms
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        cred_path = storage_path(config.credentials_path)
        user = username if username else ui.prompt("username: ")
        pwd = password if password else ui.hidden_prompt("password: ")
        comms.login(ui, user, pwd)
        token = comms.token

        if os.path.exists(cred_path):
            os.remove(cred_path)
        with open(cred_path, "w") as f:
            f.write(token)

        os.chmod(cred_path, stat.S_IREAD)
