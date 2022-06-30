from django.test import TestCase
from django.test import override_settings


class MedPerfTest(TestCase):
    """Common settings module for MedPerf APIs"""

    def setUp(self):
        # Disable SSL Redirect during tests
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
