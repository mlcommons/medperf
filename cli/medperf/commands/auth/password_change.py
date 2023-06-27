import medperf.config as config
from medperf.exceptions import InvalidArgumentError
from email_validator import validate_email, EmailNotValidError


class PasswordChange:
    @staticmethod
    def run(email: str):
        """Change the user's password. Must be logged in"""

        email = email if email else config.ui.prompt("Please type your email: ")
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidArgumentError(str(e))

        config.auth.change_password(email)
