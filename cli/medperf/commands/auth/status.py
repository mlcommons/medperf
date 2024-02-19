import medperf.config as config
from medperf.account_management import read_user_account


class Status:
    @staticmethod
    def run():
        """Shows the currently logged in user."""
        account_info = read_user_account()
        if account_info is None:
            config.ui.print("You are not logged in")
            return

        email = account_info["email"]
        config.ui.print(f"Logged in user email address: {email}")
