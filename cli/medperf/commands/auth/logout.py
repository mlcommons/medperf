import medperf.config as config
from medperf.utils import delete_current_user


class Logout:
    @staticmethod
    def run():
        """Login to the medperf server. Must be done only once."""

        config.auth.logout()

        # unset user's medperf server ID
        delete_current_user()
