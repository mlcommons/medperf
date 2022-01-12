import os
import stat
import getpass

from medperf.ui import UI
from medperf.comms import Comms
import medperf.config as config
from medperf.utils import storage_path


class Login:
    @staticmethod
    def run(comms: Comms, ui: UI):
        """Login to the medperf server. Must be done only once.
        """
        cred_path = storage_path(config.credentials_path)
        user = ui.prompt("username: ")
        pwd = ui.hidden_prompt("password: ")
        comms.login(user, pwd, ui)
        token = comms.token

        if os.path.exists(cred_path):
            os.remove(cred_path)
        with open(cred_path, "w") as f:
            f.write(token)

        os.chmod(cred_path, stat.S_IREAD)
