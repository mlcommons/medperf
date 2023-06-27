import medperf.config as config
from medperf.utils import validate_password
from medperf.exceptions import InvalidArgumentError
from email_validator import validate_email, EmailNotValidError


class Signup:
    @staticmethod
    def run(email: str, password: str):
        """Change the user's password. Must be logged in"""

        config.ui.print(config.password_policy_msg)

        # Email
        email = email if email else config.ui.prompt("Please type your email: ")
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidArgumentError(str(e))

        # Password
        if not password:
            password1 = config.ui.hidden_prompt("Please type your password: ")
            password2 = config.ui.hidden_prompt("Please type again your password: ")
            if password1 != password2:
                raise InvalidArgumentError(
                    "The passwords you typed don't match. Please try again."
                )
            password = password1
        validate_password(password)

        # Signup
        config.auth.signup(email, password)
