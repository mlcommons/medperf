from medperf.config_management import config


class Logout:
    @staticmethod
    def run():
        """Revoke the currently active login state."""

        config.auth.logout()
