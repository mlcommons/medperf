from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class MlCubeTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        mlcube_owner = "mlcube_owner"
        other_user = "other_user"

        self.create_user(mlcube_owner)
        self.create_user(other_user)

        # setup globals
        self.mlcube_owner = mlcube_owner
        self.other_user = other_user
        self.url = self.api_prefix + "/mlcubes/{0}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "mlcube_owner"},
        {"actor": "other_user"},
    ]
)
class MlCubeGetTest(MlCubeTest):
    """Test module for GET /mlcubes/<pk>"""

    def setUp(self):
        super(MlCubeGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.mlcube_owner)
        testmlcube = self.mock_mlcube()
        testmlcube = self.create_mlcube(testmlcube).data
        self.testmlcube = testmlcube
        self.set_credentials(self.actor)

    def test_generic_get_mlcube(self):
        # Arrange
        mlcube_id = self.testmlcube["id"]
        url = self.url.format(mlcube_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in self.testmlcube:
                self.assertEqual(self.testmlcube[k], v, f"Unexpected value for {k}")

    def test_mlcube_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@parameterized_class(
    [
        {"actor": "mlcube_owner"},
    ]
)
class MlCubePutTest(MlCubeTest):
    """Test module for PUT /mlcubes/<pk>"""

    def setUp(self):
        super(MlCubePutTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_put_modifies_editable_fields_in_development(self):
        # Arrange
        testmlcube = self.mock_mlcube(state="DEVELOPMENT")
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = {
            "name": "newtestmlcube",
            "git_mlcube_url": "newstring",
            "mlcube_hash": "newstring",
            "git_parameters_url": "newstring",
            "parameters_hash": "newstring",
            "image_tarball_url": "new",
            "image_tarball_hash": "new",
            "image_hash": {},
            "additional_files_tarball_url": "newstring",
            "additional_files_tarball_hash": "newstring",
            "state": "OPERATION",
            "is_valid": False,
            "metadata": {"newkey": "newvalue"},
            "user_metadata": {"newkey2": "newvalue2"},
        }
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, newtestmlcube, format="json")

        # Assert
        print(f"{response.status_code=}")
        print(f"{response.content=}")
        print(f"{response.json()=}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in newtestmlcube:
                self.assertEqual(newtestmlcube[k], v, f"{k} was not modified")

    def test_put_modifies_editable_fields_in_operation(self):
        # Arrange
        testmlcube = self.mock_mlcube(state="OPERATION")
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = {
            "additional_files_tarball_url": "newurl",
            "git_mlcube_url": "newurl",
            "git_parameters_url": "newurl",
            "is_valid": False,
            "user_metadata": {"newkey": "newval"},
        }
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, newtestmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in newtestmlcube:
                self.assertEqual(newtestmlcube[k], v, f"{k} was not modified")

    def test_put_modifies_image_tarball_url_in_operation(self):
        # Arrange
        testmlcube = self.mock_mlcube(
            state="OPERATION",
            image_hash="",
            image_tarball_url="url",
            image_tarball_hash="hash",
        )
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = {
            "image_tarball_url": "newurl",
        }
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, newtestmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in newtestmlcube:
                self.assertEqual(newtestmlcube[k], v, f"{k} was not modified")

    def test_put_does_not_modify_non_editable_fields_in_operation(self):
        # Arrange
        testmlcube = self.mock_mlcube(state="OPERATION")
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = {
            "name": "newtestmlcube",
            "mlcube_hash": "newstring",
            "parameters_hash": "newstring",
            "image_hash": {"default": "newhash"},
            "additional_files_tarball_hash": "newstring",
            "state": "DEVELOPMENT",
            "metadata": {"newkey": "newvalue"},
        }

        url = self.url.format(testmlcube["id"])

        for key in newtestmlcube:
            # Act
            response = self.client.put(url, {key: newtestmlcube[key]}, format="json")
            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"{key} was modified",
            )

    def test_put_does_not_modify_non_editable_fields_in_operation_special_case(self):
        """This test is the same as the previous one, except that it tries to modify
        image_tarball_hash, which should be accompanied by setting the image_hash
        to blank and adding image_tarball_url to work successfully in development.
        """
        # Arrange
        testmlcube = self.mock_mlcube(state="OPERATION")
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = {
            "image_tarball_url": "newurl",
            "image_tarball_hash": "new",
            "image_hash": {"default": ""},
        }

        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, newtestmlcube, format="json")

        # Assert
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "image_tarball_hash was modified",
        )

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_does_not_modify_readonly_fields_in_both_states(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(state=state)
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = {"owner": 5, "created_at": "time", "modified_at": "time"}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, newtestmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in newtestmlcube.items():
            self.assertNotEqual(v, response.data[k], f"{k} was modified")

    @parameterized.expand(
        [
            ("image_hash",),
            ("additional_files_tarball_hash",),
            ("mlcube_hash",),
            ("parameters_hash",),
        ]
    )
    def test_put_respects_rules_of_duplicate_mlcubes_with_image_hash(self, field):
        """Testing the model unique_together constraint"""
        # Arrange
        testmlcube = self.mock_mlcube()
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = self.mock_mlcube(
            name="newname", state="DEVELOPMENT", **{field: "newvalue"}
        )
        newtestmlcube = self.create_mlcube(newtestmlcube).data

        put_body = {field: testmlcube[field]}
        url = self.url.format(newtestmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ("image_tarball_hash",),
            ("additional_files_tarball_hash",),
            ("mlcube_hash",),
            ("parameters_hash",),
        ]
    )
    def test_put_respects_rules_of_duplicate_mlcubes_with_image_tarball_hash(
        self, field
    ):
        """Testing the model unique_together constraint"""
        # Arrange
        testmlcube = self.mock_mlcube(
            image_hash="", image_tarball_url="url", image_tarball_hash="hash"
        )
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = self.mock_mlcube(
            name="newname",
            state="DEVELOPMENT",
            image_hash="",
            image_tarball_url="url",
            **{"image_tarball_hash": "hash", field: "newvalue"},
        )
        newtestmlcube = self.create_mlcube(newtestmlcube).data

        put_body = {field: testmlcube[field]}
        url = self.url.format(newtestmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_respects_unique_name(self):
        # Arrange
        testmlcube = self.mock_mlcube()
        testmlcube = self.create_mlcube(testmlcube).data

        newtestmlcube = self.mock_mlcube(
            state="DEVELOPMENT", name="newname", mlcube_hash="newhash"
        )
        newtestmlcube = self.create_mlcube(newtestmlcube).data

        put_body = {"name": testmlcube["name"]}
        url = self.url.format(newtestmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_adding_image_tarball_when_image_hash_is_present(
        self, state
    ):
        # Arrange
        testmlcube = self.mock_mlcube(state=state)
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"image_tarball_url": "url", "image_tarball_hash": "hash"}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_adding_image_hash_when_image_tarball_is_present(
        self, state
    ):
        # Arrange
        testmlcube = self.mock_mlcube(
            state=state,
            image_hash="",
            image_tarball_url="url",
            image_tarball_hash="hash",
        )
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"image_hash": "hash"}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_adding_parameters_url_without_hash(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(
            state=state, git_parameters_url="", parameters_hash=""
        )
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"git_parameters_url": "url"}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_adding_additional_files_url_without_hash(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(
            state=state,
            additional_files_tarball_url="",
            additional_files_tarball_hash="",
        )
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"additional_files_tarball_url": "url"}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_adding_image_tarball_url_without_hash(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(
            state=state,
            image_tarball_url="",
            image_tarball_hash="",
        )
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"image_hash": {"default": ""}, "image_tarball_url": "url"}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_clearing_parameters_hash_without_url(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(state=state)
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"parameters_hash": ""}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_clearning_additional_files_hash_without_url(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(state=state)
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"additional_files_tarball_hash": ""}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_put_doesnot_allow_clearing_image_tarball_hash_without_url(self, state):
        # Arrange
        testmlcube = self.mock_mlcube(
            state=state,
            image_tarball_url="url",
            image_tarball_hash="hash",
            image_hash="",
        )
        testmlcube = self.create_mlcube(testmlcube).data

        put_body = {"image_tarball_hash": ""}
        url = self.url.format(testmlcube["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class MlCubeDeleteTest(MlCubeTest):
    def setUp(self):
        super(MlCubeDeleteTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.mlcube_owner)
        testmlcube = self.mock_mlcube()
        testmlcube = self.create_mlcube(testmlcube).data
        self.testmlcube = testmlcube

        self.set_credentials(self.actor)

    def test_deletion_works_as_expected(self):
        # Arrange
        url = self.url.format(self.testmlcube["id"])

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionTest(MlCubeTest):
    """Test module for permissions of /mlcubes/{pk} endpoint
    Non-permitted actions:
        GET: for unauthenticated users
        DELETE: for all users except admin
        PUT: for all users except mlcube owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

        self.set_credentials(self.mlcube_owner)
        testmlcube = self.mock_mlcube()
        testmlcube = self.create_mlcube(testmlcube).data

        self.testmlcube = testmlcube
        self.url = self.url.format(self.testmlcube["id"])

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
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange

        newtestmlcube = {
            "name": "newtestmlcube",
            "git_mlcube_url": "newstring",
            "mlcube_hash": "newstring",
            "git_parameters_url": "newstring",
            "parameters_hash": "newstring",
            "image_tarball_url": "new",
            "image_tarball_hash": "new",
            "image_hash": {"default": ""},
            "additional_files_tarball_url": "newstring",
            "additional_files_tarball_hash": "newstring",
            "state": "OPERATION",
            "is_valid": False,
            "metadata": {"newkey": "newvalue"},
            "user_metadata": {"newkey2": "newvalue2"},
            "owner": 5,
            "created_at": "time",
            "modified_at": "time",
        }
        self.set_credentials(user)

        for key in newtestmlcube:
            # Act
            response = self.client.put(
                self.url, {key: newtestmlcube[key]}, format="json"
            )
            # Assert
            self.assertEqual(
                response.status_code,
                expected_status,
                f"{key} was modified",
            )

    @parameterized.expand(
        [
            ("mlcube_owner", status.HTTP_403_FORBIDDEN),
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
