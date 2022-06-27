import os

from medperf.ui import UI
from medperf.comms import Comms
import medperf.config as config
from medperf.utils import pretty_error, storage_path


class PasswordChange:
    @staticmethod
    def run(comms: Comms, ui: UI):
        """Change the user's password. Must be logged in
        """
        pwd = ui.hidden_prompt("Please type your new password: ")
        pwd_repeat = ui.hidden_prompt("Please retype your new password: ")
        if pwd != pwd_repeat:
            pretty_error(
                "The passwords you typed don't match. Please try again.",
                ui,
                clean=False,
                add_instructions=False,
            )

        comms.change_password(pwd)
        cred_path = storage_path(config.credentials_path)
        os.remove(cred_path)
        ui.print("Password changed. Please log back in with medperf login")
