import medperf.config as config


class Login:
    @staticmethod
    def run(email: str = None):
        """Authenticate to be able to access the MedPerf server. A verification link will
        be provided and should be open in a browser to complete the login process."""
        if not email:
            email = config.ui.prompt("Please type your email: ")
        config.auth.login(email)
