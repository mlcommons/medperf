import medperf.config as config
from medperf.account_management import read_user_account
from medperf.exceptions import MedperfException


class Status:
    @staticmethod
    def run():
        """Shows the currently logged in user."""
        try:
            account_info = read_user_account()
        except MedperfException as e:
            # TODO: create a specific exception about unauthenticated client
            config.ui.print(str(e))
            return

        email = account_info["email"]
        config.ui.print(f"Logged in user email address: {email}")
