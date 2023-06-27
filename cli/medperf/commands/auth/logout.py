import medperf.config as config
from medperf.utils import unset_user_medperf_id


class Logout:
    @staticmethod
    def run():
        """Revoke the currently active login state."""

        config.auth.logout()

        # unset user's medperf server ID
        unset_user_medperf_id()
