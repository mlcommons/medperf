import os

import medperf.config as config
from medperf.utils import storage_path
from medperf.exceptions import InvalidArgumentError


class PasswordChange:
    @staticmethod
    def run():
        """Change the user's password. Must be logged in
        """
        comms = config.comms
        ui = config.ui
        pwd = ui.hidden_prompt("Please type your new password: ")
        pwd_repeat = ui.hidden_prompt("Please retype your new password: ")
        if pwd != pwd_repeat:
            raise InvalidArgumentError(
                "The passwords you typed don't match. Please try again."
            )

        comms.change_password(pwd)
        cred_path = storage_path(config.credentials_path)
        os.remove(cred_path)
        ui.print("Password changed. Please log back in with medperf login")
