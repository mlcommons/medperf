import medperf.config as config
from medperf.exceptions import InvalidArgumentError
from email_validator import validate_email, EmailNotValidError


class Login:
    @staticmethod
    def run(email: str = None):
        """Authenticate to be able to access the MedPerf server. A verification link will
        be provided and should be open in a browser to complete the login process."""
        if not email:
            email = config.ui.prompt("Please type your email: ")
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidArgumentError(str(e))
        config.auth.login(email)
