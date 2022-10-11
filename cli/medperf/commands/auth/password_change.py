import os

import medperf.config as config
from medperf.utils import pretty_error, storage_path


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
            pretty_error(
                "The passwords you typed don't match. Please try again.",
                clean=False,
                add_instructions=False,
            )

        passchange_successful = comms.change_password(pwd)
        if passchange_successful:
            cred_path = storage_path(config.credentials_path)
            os.remove(cred_path)
            ui.print("Password changed. Please log back in with medperf login")
        else:
            pretty_error("Unable to change the current password")
