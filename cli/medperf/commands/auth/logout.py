import medperf.config as config


class Logout:
    @staticmethod
    def run():
        """Revoke the currently active login state."""

        config.auth.logout()
