from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class CertificateTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        cert_owner = "cert_owner"
        ca_owner = "ca_owner"
        other_user = "other_user"

        self.create_user(cert_owner)
        self.create_user(ca_owner)
        self.create_user(other_user)

        # create CA
        self.set_credentials(ca_owner)
        ca = self.mock_ca()
        ca = self.create_ca(ca).data

        # setup globals
        self.cert_owner = cert_owner
        self.ca_owner = ca_owner
        self.other_user = other_user
        self.ca_id = ca["id"]
        self.url = self.api_prefix + "/certificates/{0}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "cert_owner"},
    ]
)
class CertificateGetTest(CertificateTest):
    """Test module for GET /certificates/<pk>"""

    def setUp(self):
        super(CertificateGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.cert_owner)
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate = self.create_certificate(testcertificate).data
        self.testcertificate = testcertificate
        self.set_credentials(self.actor)

    def test_generic_get_certificate(self):
        # Arrange
        certificate_id = self.testcertificate["id"]
        url = self.url.format(certificate_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in self.testcertificate:
                self.assertEqual(
                    self.testcertificate[k], v, f"Unexpected value for {k}"
                )

    def test_certificate_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        # TODO: fixme after refactoring permissions. should be 404
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@parameterized_class(
    [
        {"actor": "cert_owner"},
    ]
)
class CertificatePutTest(CertificateTest):
    """Test module for PUT /certificates/<pk>"""

    def setUp(self):
        super(CertificatePutTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_put_does_not_modify_non_editable_fields(self):
        """Testing the serializer validation rules"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate = self.create_certificate(testcertificate).data

        # Try to modify other fields
        put_body = {
            "name": "newname",
            "certificate_content_base64": "newcontent",
            "ca": self.ca_id,
        }
        url = self.url.format(testcertificate["id"])

        for key, val in put_body.items():
            # Act
            response = self.client.put(url, {key: val}, format="json")

            # Assert
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([(True,), (False,)])
    def test_put_can_only_set_is_valid_to_false(self, original_is_valid):
        """Testing the serializer validation rules"""
        # Arrange
        testcertificate = self.mock_certificate(
            ca=self.ca_id, is_valid=original_is_valid
        )
        testcertificate = self.create_certificate(testcertificate).data

        # Try to set is_valid to True (should fail even though it's already True)
        put_body = {"is_valid": True}
        url = self.url.format(testcertificate["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_can_invalidate_certificate(self):
        """Testing the valid scenario for invalidating"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate = self.create_certificate(testcertificate).data

        put_body = {"is_valid": False}
        url = self.url.format(testcertificate["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_valid"], False)

    def test_put_cannot_modify_multiple_fields_including_is_valid(self):
        """Testing the serializer validation rules"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate = self.create_certificate(testcertificate).data

        # Try to modify is_valid and another field
        put_body = {
            "is_valid": False,
            "name": "newname",
        }
        url = self.url.format(testcertificate["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_readonly_fields_are_not_modified(self):
        """Testing the serializer rules"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate = self.create_certificate(testcertificate).data

        readonly = {
            "owner": 999,
            "created_at": "some time",
            "modified_at": "some time",
        }
        put_body = {"is_valid": False}
        put_body.update(readonly)
        url = self.url.format(testcertificate["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )


class PermissionTest(CertificateTest):
    """Test module for permissions of /certificates/<pk> endpoint
    Non-permitted actions:
        GET: for all users except certificate owner and admin
        PUT: for all users except certificate owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.cert_owner)
        testcertificate = self.mock_certificate(ca=self.ca_id)
        self.testcertificate = self.create_certificate(testcertificate).data
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        url = self.url.format(self.testcertificate["id"])

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, expected_status)

    @parameterized.expand(
        [
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        put_body = {"is_valid": False}
        url = self.url.format(self.testcertificate["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, expected_status)
