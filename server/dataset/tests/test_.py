from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class DatasetTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        data_owner = "data_owner"
        prep_mlcube_owner = "prep_mlcube_owner"

        self.create_user(data_owner)
        self.create_user(prep_mlcube_owner)

        # create prep mlcube
        self.set_credentials(prep_mlcube_owner)
        data_preproc_mlcube = self.mock_mlcube()
        response = self.create_mlcube(data_preproc_mlcube)

        # setup globals
        self.data_owner = data_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.data_preproc_mlcube_id = response.data["id"]
        self.url = self.api_prefix + "/datasets/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "prep_mlcube_owner"},
    ]
)
class DatasetPostTest(DatasetTest):
    """Test module for POST /datasets"""

    def setUp(self):
        super(DatasetPostTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_created_dataset_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )

        # Act
        response = self.client.post(self.url, testdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for k, v in response.data.items():
            if k in testdataset:
                self.assertEqual(testdataset[k], v, f"Unexpected value for {k}")

    def test_default_values_are_as_expected(self):
        """Testing the model fields rules"""
        # Arrange
        default_values = {
            "is_valid": True,
            "state": "DEVELOPMENT",
            "generated_metadata": {},
            "user_metadata": {},
            "description": "",
            "location": "",
            "report": {},
        }
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        for key in default_values:
            if key in testdataset:
                del testdataset[key]

        # Act
        response = self.client.post(self.url, testdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in default_values.items():
            self.assertEqual(
                val, response.data[key], f"Unexpected default value for {key}"
            )

    def test_readonly_fields(self):
        """Testing the serializer rules"""
        # Arrange
        readonly = {
            "owner": 55,
            "created_at": "time",
            "modified_at": "time2",
            "state": "OPERATION",
        }
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        testdataset.update(readonly)

        # Act
        response = self.client.post(self.url, testdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "prep_mlcube_owner"},
        {"actor": "other_user"},
    ]
)
class DatasetGetListTest(DatasetTest):
    """Test module for GET /datasets/ endpoint"""

    def setUp(self):
        super(DatasetGetListTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.data_owner)
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        testdataset = self.create_dataset(testdataset).data

        other_user = "other_user"
        self.create_user("other_user")
        self.other_user = other_user

        self.testdataset = testdataset
        self.private_fields = ["owner", "report"]
        self.set_credentials(self.actor)

    def test_generic_get_dataset_list(self):
        # Arrange
        dataset_id = self.testdataset["id"]

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], dataset_id)

    def test_get_dataset_list_private_fields(self):
        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for dataset in response.data["results"]:
            for key in dataset:
                self.assertNotIn(
                    key, self.private_fields, f"{key} shouldn't be visible"
                )


class PermissionTest(DatasetTest):
    """Test module for permissions of /datasets/ endpoint
    Non-permitted actions: both GET and POST for unauthenticated users."""

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.data_owner)
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        self.testdataset = testdataset

    @parameterized.expand(
        [
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(self.data_owner)
        self.create_dataset(self.testdataset)
        self.set_credentials(user)

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand(
        [
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_post_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.post(self.url, self.testdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)
