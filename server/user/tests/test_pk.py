from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized


class UserTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        user1 = 1
        user2 = 2

        self.create_user(user1)
        self.create_user(user2)

        self.user1 = 1
        self.user2 = 2

        self.url = self.api_prefix + "/users/{0}/"
        self.set_credentials(None)


class PermissionTest(UserTest):
    """Test module for permissions of /users/<pk> endpoint
    Non-permitted actions:
        GET: for all users except admin and the user themselves
        PUT: for all users except admin
        DELETE: for all users except admin


    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.user1)
        user1_id = self.client.get(self.api_prefix + "/me/").data["id"]
        self.url = self.url.format(user1_id)
        self.set_credentials(None)

    @parameterized.expand(
        [
            (2, status.HTTP_403_FORBIDDEN),
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

    @parameterized.expand(
        [
            (1, status.HTTP_403_FORBIDDEN),
            (2, status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)

        fields = {
            "username": "new",
            "email": "new",
            "first_name": "new",
            "last_name": "new",
        }
        for field in fields:
            # Act
            response = self.client.put(self.url, {field: fields[field]}, format="json")

            # Assert
            self.assertEqual(
                response.status_code, expected_status, f"{field} was modified"
            )

    @parameterized.expand(
        [
            (1, status.HTTP_403_FORBIDDEN),
            (2, status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_delete_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.delete(self.url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
