from medperf import settings
from medperf.config_management import config
from medperf.account_management import read_user_account
from medperf.exceptions import InvalidArgumentError, MedperfException
from email_validator import validate_email, EmailNotValidError


def raise_if_logged_in():
    account_info = read_user_account()
    if account_info is not None:
        raise MedperfException(
            f"You are already logged in as {account_info['email']}."
            " Logout before logging in again"
        )


class Login:
    @staticmethod
    def run(email: str = None):
        """Authenticate to be able to access the MedPerf server. A verification link will
        be provided and should be open in a browser to complete the login process."""
        raise_if_logged_in()
        if not email:
            email = config.ui.prompt("Please type your email: ")
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidArgumentError(str(e))
        settings.auth.login(email)
