import medperf.config as config
from medperf.utils import read_config, write_config
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
        config_p = read_config()
        del config_p.active_profile[config.credentials_keyword]
        write_config(config_p)
        ui.print("Password changed. Please log back in with medperf login")
