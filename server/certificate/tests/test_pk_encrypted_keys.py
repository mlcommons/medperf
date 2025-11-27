from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class CertificateTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        cert_owner = "cert_owner"
        ca_owner = "ca_owner"
        key_owner = "key_owner"
        other_user = "other_user"

        self.create_user(cert_owner)
        self.create_user(ca_owner)
        self.create_user(key_owner)
        self.create_user(other_user)

        # create CA (uses mlcube ID 1 which exists from migrations)
        self.set_credentials(ca_owner)
        ca = self.mock_ca()
        ca = self.create_ca(ca).data

        # create certificate
        self.set_credentials(cert_owner)
        certificate = self.mock_certificate(ca=ca["id"])
        certificate = self.create_certificate(certificate).data

        # create container mlcubes for encrypted keys (owned by key_owner)
        self.set_credentials(key_owner)
        container1 = self.mock_mlcube(
            name="container1", container_config={"container1hash": "value"}
        )
        container1 = self.create_mlcube(container1).data

        container2 = self.mock_mlcube(
            name="container2", container_config={"container2hash": "value"}
        )
        container2 = self.create_mlcube(container2).data

        # create encrypted keys for the certificate (owned by key_owner)
        key1 = self.mock_encrypted_key(
            certificate=certificate["id"], container=container1["id"]
        )
        key2 = self.mock_encrypted_key(
            certificate=certificate["id"], container=container2["id"], name="key2"
        )
        key1, key2 = self.create_encrypted_keys([key1, key2]).data

        # setup globals
        self.cert_owner = cert_owner
        self.ca_owner = ca_owner
        self.key_owner = key_owner
        self.other_user = other_user
        self.certificate_id = certificate["id"]
        self.container1_id = container1["id"]
        self.container2_id = container2["id"]
        self.key1_id = key1["id"]
        self.key2_id = key2["id"]
        self.url = self.api_prefix + "/certificates/{0}/encrypted_keys/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "cert_owner"},
    ]
)
class CertificateEncryptedKeysGetTest(CertificateTest):
    """Test module for GET /certificates/<pk>/encrypted_keys/"""

    def setUp(self):
        super(CertificateEncryptedKeysGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_generic_get_encrypted_keys(self):
        # Arrange
        url = self.url.format(self.certificate_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        returned_ids = [key["id"] for key in response.data["results"]]
        self.assertIn(self.key1_id, returned_ids)
        self.assertIn(self.key2_id, returned_ids)

    def test_certificate_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_only_keys_for_specified_certificate(self):
        """Ensure we only get keys for the requested certificate"""
        # Arrange - create another certificate with keys
        self.set_credentials(self.other_user)
        ca2 = self.mock_ca(name="ca2")
        ca2 = self.create_ca(ca2).data

        cert2 = self.mock_certificate(ca=ca2["id"], name="cert2")
        cert2 = self.create_certificate(cert2).data

        # Create a key for the other certificate (by key_owner)
        self.set_credentials(self.key_owner)
        container3 = self.mock_mlcube(
            name="container3", container_config={"container3hash": "value"}
        )
        container3 = self.create_mlcube(container3).data

        key3 = self.mock_encrypted_key(
            certificate=cert2["id"], container=container3["id"], name="key3"
        )
        self.create_encrypted_keys([key3])

        # Switch back to cert_owner
        self.set_credentials(self.cert_owner)
        url = self.url.format(self.certificate_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        returned_ids = [key["id"] for key in response.data["results"]]
        self.assertIn(self.key1_id, returned_ids)
        self.assertIn(self.key2_id, returned_ids)


class PermissionTest(CertificateTest):
    """Test module for permissions of /certificates/<pk>/encrypted_keys/ endpoint
    Non-permitted actions:
        GET: for all users except certificate owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

    @parameterized.expand(
        [
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("key_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        url = self.url.format(self.certificate_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
