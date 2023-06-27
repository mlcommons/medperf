import medperf.config as config
from medperf.utils import unset_user_medperf_id


class Login:
    @staticmethod
    def run():
        """Authenticate to be able to access the MedPerf server. A verification link will
        be provided and should be open in a browser to complete the login process."""

        config.auth.login()

        # unset user's medperf server ID
        unset_user_medperf_id()
