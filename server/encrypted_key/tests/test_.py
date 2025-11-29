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
        self.url = self.api_prefix + "/encrypted_keys/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class EncryptedKeyGetListTest(EncryptedKeyTest):
    """Test module for GET /encrypted_keys/ endpoint"""

    def setUp(self):
        super(EncryptedKeyGetListTest, self).setUp()
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

    def test_generic_get_encrypted_key_list(self):
        # Arrange
        key_id = self.testkey["id"]

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], key_id)


class PermissionTest(EncryptedKeyTest):
    """Test module for permissions of /encrypted_keys/ endpoint
    Non-permitted actions:
        GET: for all users except admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.container_owner)
        self.testkeys_data = [
            {
                "name": "testkey",
                "certificate": self.certificate_id,
                "container": self.container_id,
                "encrypted_key_base64": "dGVzdF9lbmNyeXB0ZWRfa2V5X2NvbnRlbnQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        self.create_encrypted_keys(self.testkeys_data)
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("container_owner", status.HTTP_403_FORBIDDEN),
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, exp_status)
