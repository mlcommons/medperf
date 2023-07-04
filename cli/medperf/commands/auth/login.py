import medperf.config as config
from medperf.utils import unset_user_medperf_id


class Login:
    @staticmethod
    def run():
        """Authenticate to be able to access the MedPerf server. A verification link will
        be provided and should be open in a browser to complete the login process."""

        config.auth.login()

        # Some logic may have cached the user's MedPerf server ID in the local storage.
        # After login, we need to make sure this ID is removed so that later when that same
        # logic tries to use the user's MedPerf server ID, it will call the server to get
        # the currently logged in user's MedPerf server ID, not a cached one which may
        # belong to the previously logged in user.
        unset_user_medperf_id()
