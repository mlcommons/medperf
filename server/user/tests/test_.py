from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized


class UserTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        user1 = "user1"
        user2 = "user2"

        self.create_user(user1)
        self.create_user(user2)

        self.url = self.api_prefix + "/users/"
        self.set_credentials(None)


class PermissionTest(UserTest):
    """Test module for permissions of /users/ endpoint
    Non-permitted actions:
        GET: for all users except admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("user1", status.HTTP_403_FORBIDDEN),
            ("user2", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
