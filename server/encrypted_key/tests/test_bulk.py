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

        # create invalid certificate for testing
        invalid_cert = self.mock_certificate(
            ca=ca["id"], name="invalid_cert", is_valid=False
        )
        invalid_cert = self.create_certificate(invalid_cert).data
        # Invalidate it
        self.client.put(
            self.api_prefix + f"/certificates/{invalid_cert['id']}/",
            {"is_valid": False},
            format="json",
        )

        # create container mlcubes
        self.set_credentials(container_owner)
        container1 = self.mock_mlcube(
            name="container1", container_config={"container1hash": "value"}
        )
        container1 = self.create_mlcube(container1).data

        container2 = self.mock_mlcube(
            name="container2", container_config={"container2hash": "value"}
        )
        container2 = self.create_mlcube(container2).data

        # setup globals
        self.container_owner = container_owner
        self.cert_owner = cert_owner
        self.ca_owner = ca_owner
        self.other_user = other_user
        self.certificate_id = certificate["id"]
        self.invalid_certificate_id = invalid_cert["id"]
        self.container1_id = container1["id"]
        self.container2_id = container2["id"]
        self.url = self.api_prefix + "/encrypted_keys/bulk/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "container_owner"},
    ]
)
class EncryptedKeyBulkPostTest(EncryptedKeyTest):
    """Test module for POST /encrypted_keys/bulk/"""

    def setUp(self):
        super(EncryptedKeyBulkPostTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_bulk_create_encrypted_keys(self):
        """Testing the valid scenario for bulk creation"""
        # Arrange
        keys_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            },
            {
                "name": "key2",
                "certificate": self.certificate_id,
                "container": self.container2_id,
                "encrypted_key_base64": "a2V5Ml9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            },
        ]

        # Act
        response = self.client.post(self.url, keys_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)
        for i, key_data in enumerate(keys_data):
            for k, v in key_data.items():
                self.assertEqual(
                    response.data[i][k], v, f"Unexpected value for {k} in key {i}"
                )

    def test_bulk_create_fails_with_invalid_certificate(self):
        """Testing the serializer validation rules"""
        # Arrange
        keys_data = [
            {
                "name": "key1",
                "certificate": self.invalid_certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]

        # Act
        response = self.client.post(self.url, keys_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_readonly_fields(self):
        """Testing the serializer rules"""
        # Arrange
        readonly = {
            "owner": 999,
            "created_at": "some time",
            "modified_at": "some time",
        }
        keys_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        keys_data[0].update(readonly)

        # Act
        response = self.client.post(self.url, keys_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[0][key], f"readonly field {key} was modified"
            )

    def test_bulk_create_respects_unique_constraint(self):
        """Testing the model UniqueConstraint on (certificate, container)"""
        # Arrange - create first key
        key1_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        self.client.post(self.url, key1_data, format="json")

        # Try to create another valid key for same certificate and container
        key2_data = [
            {
                "name": "key2_different_name",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "ZGlmZmVyZW50X2Jhc2U2NA==",
                "is_valid": True,
                "metadata": {},
            }
        ]

        # Act
        response = self.client.post(self.url, key2_data, format="json")

        # Assert - should fail due to unique constraint
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_respects_unique_constraint_2(self):
        """Testing the model UniqueConstraint on (certificate, container)
        when both keys are created simultanuously"""
        # Arrange - create first key
        key1_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        # Try to create another valid key for same certificate and container
        key2_data = [
            {
                "name": "key2_different_name",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "ZGlmZmVyZW50X2Jhc2U2NA==",
                "is_valid": True,
                "metadata": {},
            }
        ]

        # Act
        response = self.client.post(self.url, key1_data + key2_data, format="json")

        # Assert - should fail due to unique constraint
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # make sure nothing was created (all or nothing)
        self.set_credentials(self.api_admin)
        response = self.client.get(self.api_prefix + "/encrypted_keys/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 0)

    def test_bulk_create_allows_multiple_invalid_keys_for_same_cert_container(self):
        """Testing that constraint allows multiple invalid keys"""
        # Arrange - create first key and invalidate it
        key1_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        key1 = self.client.post(self.url, key1_data, format="json").data[0]

        # Invalidate it
        response = self.client.put(
            self.url,
            [
                {
                    "id": key1["id"],
                    "is_valid": False,
                    "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
                }
            ],
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create another key for same certificate and container
        key2_data = [
            {
                "name": "key2",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5Ml9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]

        # Act
        response = self.client.post(self.url, key2_data, format="json")

        # Assert - should succeed since previous key is invalid
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@parameterized_class(
    [
        {"actor": "container_owner"},
    ]
)
class EncryptedKeyBulkPutTest(EncryptedKeyTest):
    """Test module for PUT /encrypted_keys/bulk/"""

    def setUp(self):
        super(EncryptedKeyBulkPutTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.container_owner)
        keys_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            },
            {
                "name": "key2",
                "certificate": self.certificate_id,
                "container": self.container2_id,
                "encrypted_key_base64": "a2V5Ml9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            },
        ]
        self.keys = self.client.post(self.url, keys_data, format="json").data
        self.set_credentials(self.actor)

    def test_bulk_update_can_only_modify_is_valid_and_encrypted_key_base64(self):
        """Testing the serializer validation rules"""
        # Arrange - try to modify other fields
        put_data = [
            {
                "id": self.keys[0]["id"],
                "name": "newname",
                "certificate": self.certificate_id,
            }
        ]

        for key, val in put_data[0].items():
            if key == "id":
                continue
            # Act
            response = self.client.put(
                self.url, [{key: val, "id": put_data[0]["id"]}], format="json"
            )

            # Assert
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_can_only_set_is_valid_to_false(self):
        """Testing the serializer validation rules"""
        # Arrange - try to set is_valid to True
        put_data = [
            {
                "id": self.keys[0]["id"],
                "is_valid": True,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            }
        ]

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_can_invalidate_and_update_keys(self):
        """Testing the valid scenario for bulk update"""
        # Arrange
        put_data = [
            {
                "id": self.keys[0]["id"],
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            },
            {
                "id": self.keys[1]["id"],
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTJfYmFzZTY0",
            },
        ]

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bulk_update_fails_if_missing_id(self):
        """Testing error handling"""
        # Arrange - missing id field
        put_data = [
            {
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            }
        ]

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(
        [[[{"is_valid": False}]], [[{"encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0"}]]]
    )
    def test_bulk_update_fails_if_updating_is_valid_or_key_content_only(self, put_data):
        """Testing error handling"""
        # Arrange
        put_data[0].update({"id": self.keys[0]["id"]})

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_fails_if_not_all_keys_exist(self):
        """Testing the serializer validation"""
        # Arrange - include non-existent key
        put_data = [
            {
                "id": 9999,
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            },
            {
                "id": self.keys[0]["id"],
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            },
        ]

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Make sure the key wasn't changed (all or nothing)
        response = self.client.get(
            self.api_prefix + f"/encrypted_keys/{self.keys[0]['id']}/", format="json"
        )
        self.assertEqual(response.data["is_valid"], True)

    def test_bulk_update_readonly_fields_are_not_modified(self):
        """Testing the serializer rules"""
        # Arrange
        readonly = {
            "owner": 999,
            "created_at": "some time",
            "modified_at": "some time",
        }
        put_data = [
            {
                "id": self.keys[0]["id"],
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            }
        ]
        put_data[0].update(readonly)

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify by getting the key
        key = self.client.get(
            self.api_prefix + f"/encrypted_keys/{self.keys[0]['id']}/"
        ).data
        for field, val in readonly.items():
            self.assertNotEqual(val, key[field], f"readonly field {field} was modified")


class BulkPostPermissionTest(EncryptedKeyTest):
    """Test module for POST permissions of /encrypted_keys/bulk/ endpoint
    Non-permitted actions:
        POST: for all users except container owner and admin
    """

    def setUp(self):
        super(BulkPostPermissionTest, self).setUp()
        self.generic_setup()

    @parameterized.expand(
        [
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_post_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        keys_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]

        # Act
        response = self.client.post(self.url, keys_data, format="json")

        # Assert
        self.assertEqual(response.status_code, expected_status)

    @parameterized.expand(
        [
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            ("container_owner", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_post_fails_when_containers_have_different_owners(self, user, exp_status):
        """Testing that bulk create fails when user doesn't own all containers"""
        # Arrange - create a container owned by other_user
        self.set_credentials(self.other_user)
        other_container = self.mock_mlcube(
            name="other_container", container_config={"otherhash": "value"}
        )
        other_container = self.create_mlcube(other_container).data

        # Try to create keys with mixed container ownership
        self.set_credentials(user)
        keys_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,  # owned by container_owner
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            },
            {
                "name": "key2",
                "certificate": self.certificate_id,
                "container": other_container["id"],  # owned by other_user
                "encrypted_key_base64": "a2V5Ml9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            },
        ]

        # Act
        response = self.client.post(self.url, keys_data, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)


class BulkPutPermissionTest(EncryptedKeyTest):
    """Test module for PUT permissions of /encrypted_keys/bulk/ endpoint
    Non-permitted actions:
        PUT: for all users except key owner and admin
    """

    def setUp(self):
        super(BulkPutPermissionTest, self).setUp()
        self.generic_setup()
        # Create keys as container owner
        self.set_credentials(self.container_owner)
        keys_data = [
            {
                "name": "key1",
                "certificate": self.certificate_id,
                "container": self.container1_id,
                "encrypted_key_base64": "a2V5MV9iYXNlNjQ=",
                "is_valid": True,
                "metadata": {},
            }
        ]
        self.keys = self.client.post(self.url, keys_data, format="json").data
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        put_data = [
            {
                "id": self.keys[0]["id"],
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            }
        ]

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, expected_status)

    @parameterized.expand(
        [
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            ("container_owner", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_fails_when_keys_have_different_owners(self, user, exp_status):
        """Testing that bulk update fails when user doesn't own all keys"""
        # Arrange - create a key owned by other_user
        self.set_credentials(self.other_user)
        other_container = self.mock_mlcube(
            name="other_container", container_config={"otherhash": "value"}
        )
        other_container = self.create_mlcube(other_container).data

        other_keys_data = [
            {
                "name": "other_key",
                "certificate": self.certificate_id,
                "container": other_container["id"],
                "encrypted_key_base64": "b3RoZXJfa2V5X2Jhc2U2NA==",
                "is_valid": True,
                "metadata": {},
            }
        ]
        other_keys = self.client.post(self.url, other_keys_data, format="json").data

        # Try to update keys with mixed ownership
        self.set_credentials(user)
        put_data = [
            {
                "id": self.keys[0]["id"],  # owned by container_owner
                "is_valid": False,
                "encrypted_key_base64": "bmV3X2tleTFfYmFzZTY0",
            },
            {
                "id": other_keys[0]["id"],  # owned by other_user
                "is_valid": False,
                "encrypted_key_base64": "bmV3X290aGVyX2tleV9iYXNlNjQ=",
            },
        ]

        # Act
        response = self.client.put(self.url, put_data, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)
