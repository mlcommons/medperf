import os
import stat

from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.utils import storage_path


class Login:
    @staticmethod
    def run(comms: Comms, ui: UI, username: str = None, password: str = None):
        """Login to the medperf server. Must be done only once.
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
