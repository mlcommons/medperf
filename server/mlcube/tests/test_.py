from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class MlCubeTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        mlcube_owner = "mlcube_owner"
        self.create_user(mlcube_owner)

        # setup globals
        self.mlcube_owner = mlcube_owner
        self.url = self.api_prefix + "/mlcubes/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "mlcube_owner"},
    ]
)
class MlCubePostTest(MlCubeTest):
    """Test module for POST /mlcubes"""

    def setUp(self):
        super(MlCubePostTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_created_mlcube_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        testmlcube = self.mock_mlcube()

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for k, v in response.data.items():
            if k in testmlcube:
                self.assertEqual(testmlcube[k], v, f"Unexpected value for {k}")

    @parameterized.expand([(True,), (False,)])
    def test_creation_of_duplicate_name_gets_rejected(self, different_name):
        """Testing the model fields rules"""
        # Arrange
        testmlcube = self.mock_mlcube()
        self.create_mlcube(testmlcube)
        testmlcube["image_hash"] = "new string"

        if different_name:
            testmlcube["name"] = "different name"

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        if different_name:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST

        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand(
        [
            ("image_hash",),
            ("additional_files_tarball_hash",),
            ("mlcube_hash",),
            ("parameters_hash",),
            (None,),
        ]
    )
    def test_creation_of_duplicate_mlcubes_with_image_hash(self, field):
        """Testing the model unique_together constraint"""
        # Arrange
        testmlcube = self.mock_mlcube()
        self.create_mlcube(testmlcube)
        testmlcube["name"] = "new name"

        if field is not None:
            testmlcube[field] = "different string"

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        if field is not None:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST

        self.assertEqual(
            response.status_code, exp_status, f"test failed with field {field}"
        )

    @parameterized.expand(
        [
            ("image_tarball_hash",),
            ("additional_files_tarball_hash",),
            ("mlcube_hash",),
            ("parameters_hash",),
            (None,),
        ]
    )
    def test_creation_of_duplicate_mlcubes_with_image_tarball(self, field):
        """Testing the model unique_together constraint"""
        # Arrange
        testmlcube = self.mock_mlcube(
            image_hash="", image_tarball_url="string", image_tarball_hash="string"
        )
        self.create_mlcube(testmlcube)
        testmlcube["name"] = "new name"

        if field is not None:
            testmlcube[field] = "different string"

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        if field is not None:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST

        self.assertEqual(
            response.status_code, exp_status, f"test failed with field {field}"
        )

    def test_default_values_are_as_expected(self):
        """Testing the model fields rules"""
        # Arrange
        default_values = {
            "state": "DEVELOPMENT",
            "is_valid": True,
            "metadata": {},
            "user_metadata": {},
            "git_parameters_url": "",
            "image_tarball_url": "",
            "additional_files_tarball_url": "",
        }
        testmlcube = self.mock_mlcube()
        for key in default_values:
            if key in testmlcube:
                del testmlcube[key]

        # in order to allow empty urls
        testmlcube.update(
            {
                "parameters_hash": "",
                "image_tarball_hash": "",
                "additional_files_tarball_hash": "",
            }
        )
        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in default_values.items():
            self.assertEqual(
                val, response.data[key], f"unexpected default value for {key}"
            )

    def test_readonly_fields(self):
        """Testing the serializer rules"""
        # Arrange
        readonly = {
            "owner": 10,
            "created_at": "some time",
            "modified_at": "some time",
        }
        testmlcube = self.mock_mlcube()
        testmlcube.update(readonly)

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )

    @parameterized.expand([(True,), (False,)])
    def test_parameters_file_should_have_a_hash(self, url_provided):
        """Testing the serializer rules"""
        # Arrange
        testmlcube = self.mock_mlcube(parameters_hash="")
        if not url_provided:
            testmlcube["git_parameters_url"] = ""

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        if not url_provided:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand([(True,), (False,)])
    def test_additional_files_should_have_a_hash(self, url_provided):
        """Testing the serializer rules"""

        # Arrange
        testmlcube = self.mock_mlcube(additional_files_tarball_hash="")
        if not url_provided:
            testmlcube["additional_files_tarball_url"] = ""

        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        if not url_provided:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand(
        [
            (False, False, False, status.HTTP_400_BAD_REQUEST),
            (False, False, True, status.HTTP_400_BAD_REQUEST),
            (False, True, False, status.HTTP_400_BAD_REQUEST),
            (False, True, True, status.HTTP_201_CREATED),
            (True, False, False, status.HTTP_201_CREATED),
            (True, False, True, status.HTTP_400_BAD_REQUEST),
            (True, True, False, status.HTTP_400_BAD_REQUEST),
            (True, True, True, status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_image_fields_cases(
        self, image_hash, image_tarball_url, image_tarball_hash, exp_status
    ):
        """Testing the serializer rules
        The rules are simply stating that either "image_hash", or both the
        "image_tarball_url" and "image_tarball_hash", should be provided."""

        # Arrange
        testmlcube = self.mock_mlcube(
            image_hash="string" if image_hash else "",
            image_tarball_url="string" if image_tarball_url else "",
            image_tarball_hash="string" if image_tarball_hash else "",
        )
        # Act
        response = self.client.post(self.url, testmlcube, format="json")

        # Assert
        self.assertEqual(
            response.status_code,
            exp_status,
            f"test failed with image_hash={image_hash}, "
            f"image_tarball_url={image_tarball_url}, "
            f"image_tarball_hash={image_tarball_hash}",
        )


@parameterized_class(
    [
        {"actor": "mlcube_owner"},
        {"actor": "other_user"},
    ]
)
class MlCubeGetListTest(MlCubeTest):
    """Test module for GET /mlcubes/ endpoint"""

    def setUp(self):
        super(MlCubeGetListTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.mlcube_owner)
        testmlcube = self.mock_mlcube()
        testmlcube = self.create_mlcube(testmlcube).data

        other_user = "other_user"
        self.create_user("other_user")
        self.other_user = other_user

        self.testmlcube = testmlcube
        self.set_credentials(self.actor)

    def test_generic_get_mlcube_list(self):
        # Arrange
        mlcube_id = self.testmlcube["id"]

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], mlcube_id)


class PermissionTest(MlCubeTest):
    """Test module for permissions of /mlcubes/ endpoint
    Non-permitted actions: both GET and POST for unauthenticated users."""

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.mlcube_owner)
        testmlcube = self.mock_mlcube()
        self.testmlcube = testmlcube

    @parameterized.expand(
        [
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(self.mlcube_owner)
        self.create_mlcube(self.testmlcube)
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
        response = self.client.post(self.url, self.testmlcube, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)
