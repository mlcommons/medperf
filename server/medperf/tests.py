from django.test import TestCase
from django.test import override_settings
from .testing_utils import PUBLIC_KEY, setup_api_admin, create_user


class MedPerfTest(TestCase):
    """Common settings module for MedPerf APIs"""

    def setUp(self):
        SIMPLE_JWT = {
            "ALGORITHM": "RS256",
            "AUDIENCE": "https://localhost-unittests/",
            "ISSUER": "https://localhost:8000/",
            "JWK_URL": None,
            "USER_ID_FIELD": "username",
            "USER_ID_CLAIM": "sub",
            "TOKEN_TYPE_CLAIM": None,
            "JTI_CLAIM": None,
            "VERIFYING_KEY": PUBLIC_KEY,
        }

        # Disable SSL Redirect during tests and use custom jwt config
        settings_manager = override_settings(
            SECURE_SSL_REDIRECT=False, SIMPLE_JWT=SIMPLE_JWT
        )
        settings_manager.enable()
        self.admin_token = setup_api_admin()
        self.addCleanup(settings_manager.disable)

    def create_user(self, username):
        return create_user(username)
