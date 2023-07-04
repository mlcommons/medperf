import medperf.config as config
from medperf.utils import unset_medperf_user_data


class Logout:
    @staticmethod
    def run():
        """Revoke the currently active login state."""

        config.auth.logout()

        # unset user's medperf server ID
        unset_medperf_user_data()
