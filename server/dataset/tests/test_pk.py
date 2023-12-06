from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class DatasetTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        data_owner = "data_owner"
        prep_mlcube_owner = "prep_mlcube_owner"
        other_user = "other_user"

        self.create_user(data_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(other_user)

        # create prep mlcube
        self.set_credentials(prep_mlcube_owner)
        data_preproc_mlcube = self.mock_mlcube()
        response = self.create_mlcube(data_preproc_mlcube)

        # setup globals
        self.data_owner = data_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.other_user = other_user
        self.data_preproc_mlcube_id = response.data["id"]
        self.url = self.api_prefix + "/datasets/{0}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "prep_mlcube_owner"},
        {"actor": "other_user"},
    ]
)
class DatasetGetTest(DatasetTest):
    """Test module for GET /datasets/<pk>"""

    def setUp(self):
        super(DatasetGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.data_owner)
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        testdataset = self.create_dataset(testdataset).data
        self.testdataset = testdataset
        self.set_credentials(self.actor)

    def test_generic_get_dataset(self):
        # Arrange
        dataset_id = self.testdataset["id"]
        url = self.url.format(dataset_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in self.testdataset:
                self.assertEqual(self.testdataset[k], v, f"Unexpected value for {k}")

    def test_dataset_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@parameterized_class(
    [
        {"actor": "data_owner"},
    ]
)
class DatasetPutTest(DatasetTest):
    """Test module for PUT /datasets/<pk>"""

    def setUp(self):
        super(DatasetPutTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_put_modifies_editable_fields_in_development(self):
        # Arrange
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id, state="DEVELOPMENT"
        )
        testdataset = self.create_dataset(testdataset).data

        new_data_preproc_mlcube = self.mock_mlcube(
            name="new name", mlcube_hash="new hash"
        )
        new_prep_id = self.create_mlcube(new_data_preproc_mlcube).data["id"]
        newtestdataset = {
            "name": "newdataset",
            "description": "newdataset-sample",
            "location": "newstring",
            "input_data_hash": "newstring",
            "generated_uid": "newstring",
            "split_seed": 1,
            "data_preparation_mlcube": new_prep_id,
            "is_valid": False,
            "state": "OPERATION",
            "generated_metadata": {"newkey": "newvalue"},
            "user_metadata": {"newkey2": "newvalue2"},
        }
        url = self.url.format(testdataset["id"])

        # Act
        response = self.client.put(url, newtestdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newtestdataset:
                self.assertEqual(newtestdataset[k], v, f"{k} was not modified")

    def test_put_modifies_editable_fields_in_operation(self):
        # Arrange
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id, state="OPERATION"
        )
        testdataset = self.create_dataset(testdataset).data

        newtestdataset = {"is_valid": False, "user_metadata": {"newkey": "newval"}}
        url = self.url.format(testdataset["id"])

        # Act
        response = self.client.put(url, newtestdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newtestdataset:
                self.assertEqual(newtestdataset[k], v, f"{k} was not modified")

    def test_put_does_not_modify_non_editable_fields_in_operation(self):
        # Arrange
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id, state="OPERATION"
        )
        testdataset = self.create_dataset(testdataset).data

        new_data_preproc_mlcube = self.mock_mlcube(
            name="new name", mlcube_hash="new hash"
        )
        new_prep_id = self.create_mlcube(new_data_preproc_mlcube).data["id"]
        newtestdataset = {
            "name": "newdataset",
            "description": "newdataset-sample",
            "location": "newstring",
            "input_data_hash": "newstring",
            "generated_uid": "newstring",
            "split_seed": 6,
            "data_preparation_mlcube": new_prep_id,
            "state": "DEVELOPMENT",
            "generated_metadata": {"newkey": "value"},
        }

        url = self.url.format(testdataset["id"])

        for key in newtestdataset:
            # Act
            response = self.client.put(url, {key: newtestdataset[key]}, format="json")
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"{key} was modified",
            )

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_does_not_modify_readonly_fields_in_both_states(self, state):
        # Arrange
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id, state=state
        )
        testdataset = self.create_dataset(testdataset).data

        newtestdataset = {"owner": 5, "created_at": "time", "modified_at": "time"}
        url = self.url.format(testdataset["id"])

        # Act
        response = self.client.put(url, newtestdataset, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in newtestdataset.items():
            self.assertNotEqual(v, response.data[k], f"{k} was modified")

    def test_put_respects_unique_generated_uid(self):
        # Arrange
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        testdataset = self.create_dataset(testdataset).data

        newtestdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id,
            state="DEVELOPMENT",
            generated_uid="new",
        )
        newtestdataset = self.create_dataset(newtestdataset).data

        put_body = {"generated_uid": testdataset["generated_uid"]}
        url = self.url.format(newtestdataset["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class DatasetDeleteTest(DatasetTest):
    def setUp(self):
        super(DatasetDeleteTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.data_owner)
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        testdataset = self.create_dataset(testdataset).data
        self.testdataset = testdataset

        self.set_credentials(self.actor)

    def test_deletion_works_as_expected(self):
        # Arrange
        url = self.url.format(self.testdataset["id"])

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionTest(DatasetTest):
    """Test module for permissions of /datasets/{pk} endpoint
    Non-permitted actions:
        GET: for unauthenticated users
        DELETE: for all users except admin
        PUT: for all users except data owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

        self.set_credentials(self.data_owner)
        testdataset = self.mock_dataset(
            data_preparation_mlcube=self.data_preproc_mlcube_id
        )
        testdataset = self.create_dataset(testdataset).data

        self.testdataset = testdataset
        self.url = self.url.format(self.testdataset["id"])

    @parameterized.expand(
        [
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
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(self.prep_mlcube_owner)
        new_data_preproc_mlcube = self.mock_mlcube(
            name="new name", mlcube_hash="new hash"
        )
        new_prep_id = self.create_mlcube(new_data_preproc_mlcube).data["id"]
        newtestdataset = {
            "name": "newdataset",
            "description": "newdataset-sample",
            "location": "newstring",
            "input_data_hash": "newstring",
            "generated_uid": "newstring",
            "split_seed": 1,
            "data_preparation_mlcube": new_prep_id,
            "is_valid": False,
            "state": "OPERATION",
            "generated_metadata": {"newkey": "newvalue"},
            "user_metadata": {"newkey2": "newvalue2"},
            "owner": 5,
            "created_at": "time",
            "modified_at": "time",
        }
        self.set_credentials(user)

        for key in newtestdataset:
            # Act
            response = self.client.put(
                self.url, {key: newtestdataset[key]}, format="json"
            )
            # Assert
            self.assertEqual(
                response.status_code,
                expected_status,
                f"{key} was modified",
            )

    @parameterized.expand(
        [
            ("data_owner", status.HTTP_403_FORBIDDEN),
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
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
