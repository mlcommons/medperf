import medperf.config as config
from medperf.exceptions import InvalidArgumentError
from email_validator import validate_email, EmailNotValidError


class PasswordChange:
    @staticmethod
    def run(email: str):
        """Send an email for changing the password.
        The user will change their password on the web UI."""

        email = email if email else config.ui.prompt("Please type your email: ")
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidArgumentError(str(e))

        config.auth.change_password(email)
