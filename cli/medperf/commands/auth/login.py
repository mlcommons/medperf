import medperf.config as config


class Login:
    @staticmethod
    def run():
        """Authenticate to be able to access the MedPerf server. A verification link will
        be provided and should be open in a browser to complete the login process."""

        config.auth.login()
