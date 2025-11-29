from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class EncryptedKeyTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        container_owner = "container_owner"
        cert_owner = "cert_owner"
        ca_owner = "ca_owner"
        other_user = "other_user"

        self.create_user(container_owner)
        self.create_user(cert_owner)
        self.create_user(ca_owner)
        self.create_user(other_user)

        # create CA
        self.set_credentials(ca_owner)
        ca = self.mock_ca()
        ca = self.create_ca(ca).data

        # create certificate
        self.set_credentials(cert_owner)
        certificate = self.mock_certificate(ca=ca["id"])
        certificate = self.create_certificate(certificate).data

        # create container mlcube
        self.set_credentials(container_owner)
        container = self.mock_mlcube(
            name="container", container_config={"containerhash": "value"}
        )
        container = self.create_mlcube(container).data

        # setup globals
        self.container_owner = container_owner
        self.cert_owner = cert_owner
        self.ca_owner = ca_owner
        self.other_user = other_user
        self.certificate_id = certificate["id"]
        self.container_id = container["id"]
        self.url = self.api_prefix + "/encrypted_keys/{0}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "container_owner"},
    ]
)
class EncryptedKeyGetTest(EncryptedKeyTest):
    """Test module for GET /encrypted_keys/<pk>"""

    def setUp(self):
        super(EncryptedKeyGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.container_owner)
        keys_data = [
            {
                "name": "testkey",
                "certificate": self.certificate_id,
                "container": self.container_id,
                "encrypted_key_base64": "dGVzdF9lbmNyeXB0ZWRfa2V5X2NvbnRlbnQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        testkeys = self.create_encrypted_keys(keys_data).data
        self.testkey = testkeys[0]
        self.set_credentials(self.actor)

    def test_generic_get_encrypted_key(self):
        # Arrange
        key_id = self.testkey["id"]
        url = self.url.format(key_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in self.testkey:
                self.assertEqual(self.testkey[k], v, f"Unexpected value for {k}")

    def test_encrypted_key_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PermissionTest(EncryptedKeyTest):
    """Test module for permissions of /encrypted_keys/<pk> endpoint
    Non-permitted actions:
        GET: for all users except key owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.container_owner)
        keys_data = [
            {
                "name": "testkey",
                "certificate": self.certificate_id,
                "container": self.container_id,
                "encrypted_key_base64": "dGVzdF9lbmNyeXB0ZWRfa2V5X2NvbnRlbnQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        testkeys = self.create_encrypted_keys(keys_data).data
        self.testkey = testkeys[0]
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        url = self.url.format(self.testkey["id"])

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
