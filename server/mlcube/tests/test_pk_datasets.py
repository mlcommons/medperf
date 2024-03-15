from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class MlCubeTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        mlcube_owner = "mlcube_owner"
        data_owner = "data_owner"
        other_user = "other_user"

        self.create_user(mlcube_owner)
        self.create_user(data_owner)
        self.create_user(other_user)

        # create mlcube and dataset
        testmlcube = self.mock_mlcube(state="DEVELOPMENT")
        self.set_credentials(mlcube_owner)
        testmlcube = self.create_mlcube(testmlcube).data
        data = self.mock_dataset(testmlcube["id"])
        self.set_credentials(data_owner)
        data = self.create_dataset(data).data

        # setup globals
        self.mlcube_owner = mlcube_owner
        self.data_owner = data_owner
        self.other_user = other_user
        self.data_id = data["id"]
        self.mlcube_id = testmlcube["id"]

        self.url = self.api_prefix + "/mlcubes/{0}/datasets/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "mlcube_owner"},
    ]
)
class MlCubeDatasetGetListTest(MlCubeTest):
    """Test module for GET /mlcubes/<pk>/datasets/ endpoint"""

    def setUp(self):
        super(MlCubeDatasetGetListTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_generic_get_mlcube_datasets_list(self):
        # Arrange
        url = self.url.format(self.mlcube_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 1, "unexpected number of datasets"
        )

    def test_get_mlcube_datasets_list_fails_if_mlcube_is_operation(self):
        # Arrange

        # make mlcube operational
        put_body = {"state": "OPERATION"}
        url = self.api_prefix + "/mlcubes/{0}/".format(self.mlcube_id)
        response = self.client.put(url, put_body, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = self.url.format(self.mlcube_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PermissionTest(MlCubeTest):
    """Test module for permissions of /mlcubes/{pk}/datasets/ endpoint
    Non-permitted actions:
        GET: for all users except mlcube owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.url = self.url.format(self.mlcube_id)
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("data_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
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
