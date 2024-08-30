from medperf import settings


class Logout:
    @staticmethod
    def run():
        """Revoke the currently active login state."""

        settings.auth.logout()
