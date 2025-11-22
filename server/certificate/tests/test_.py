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
        self.url = self.api_prefix + "/certificates/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "cert_owner"},
    ]
)
class CertificatePostTest(CertificateTest):
    """Test module for POST /certificates"""

    def setUp(self):
        super(CertificatePostTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_created_certificate_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)

        # Act
        response = self.client.post(self.url, testcertificate, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for k, v in response.data.items():
            if k in testcertificate:
                self.assertEqual(testcertificate[k], v, f"Unexpected value for {k}")

    @parameterized.expand([(True,), (False,)])
    def test_creation_of_duplicate_name_gets_rejected(self, different_name):
        """Testing the model unique name constraint"""
        # Arrange
        self.set_credentials(self.actor)

        testcertificate = self.mock_certificate(ca=self.ca_id)
        self.create_certificate(testcertificate)
        if different_name:
            testcertificate["name"] = "different name"

        # use different ca ID for the second cert to avoid constraint failure
        self.set_credentials(self.ca_owner)
        ca2 = self.mock_ca(name="different_ca")
        ca2 = self.create_ca(ca2).data
        self.set_credentials(self.actor)

        testcertificate["ca"] = ca2["id"]

        # Act
        response = self.client.post(self.url, testcertificate, format="json")

        # Assert
        if different_name:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, exp_status)

    def test_default_values_are_as_expected(self):
        """Testing the model fields rules"""
        # Arrange
        default_values = {
            "is_valid": True,
        }
        testcertificate = self.mock_certificate(ca=self.ca_id)
        for key in default_values:
            if key in testcertificate:
                del testcertificate[key]

        # Act
        response = self.client.post(self.url, testcertificate, format="json")

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
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate.update(readonly)

        # Act
        response = self.client.post(self.url, testcertificate, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )

    def test_one_valid_certificate_per_user_and_ca_constraint(self):
        """Testing the model UniqueConstraint"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        self.create_certificate(testcertificate)

        # Create another certificate for same user and CA
        testcertificate2 = self.mock_certificate(
            ca=self.ca_id,
            name="different_name",
            certificate_content_base64="different_content",
        )

        # Act
        response = self.client.post(self.url, testcertificate2, format="json")

        # Assert - should fail due to unique constraint (one valid cert per user+ca)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_multiple_certificates_if_previous_is_invalid(self):
        """Testing that constraint allows multiple certs if previous ones are invalid"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        cert = self.create_certificate(testcertificate).data

        # Invalidate first certificate
        self.client.put(
            self.api_prefix + f"/certificates/{cert['id']}/",
            {"is_valid": False},
            format="json",
        )

        # Create another certificate for same user and CA
        testcertificate2 = self.mock_certificate(
            ca=self.ca_id,
            name="different_name",
            certificate_content_base64="different_content",
        )

        # Act
        response = self.client.post(self.url, testcertificate2, format="json")

        # Assert - should succeed since previous cert is invalid
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_certificates_for_different_ca(self):
        """Testing that same user can have valid certs for different CAs"""
        # Arrange
        testcertificate = self.mock_certificate(ca=self.ca_id)
        self.create_certificate(testcertificate)

        # Create another CA
        self.set_credentials(self.ca_owner)
        ca2 = self.mock_ca(name="different_ca")
        ca2 = self.create_ca(ca2).data

        self.set_credentials(self.actor)
        testcertificate2 = self.mock_certificate(
            ca=ca2["id"],
            name="different_name",
            certificate_content_base64="different_content",
        )

        # Act
        response = self.client.post(self.url, testcertificate2, format="json")

        # Assert - should succeed since different CA
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ],
)
class CertificateGetListTest(CertificateTest):
    """Test module for GET /certificates/ endpoint"""

    def setUp(self):
        super(CertificateGetListTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.cert_owner)
        testcertificate = self.mock_certificate(ca=self.ca_id)
        testcertificate = self.create_certificate(testcertificate).data
        self.testcertificate = testcertificate
        self.set_credentials(self.actor)

    def test_generic_get_list_certificates(self):
        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.testcertificate["id"])


class PermissionTest(CertificateTest):
    """Test module for permissions of /certificates/ endpoint"""

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.testcertificate = self.mock_certificate(ca=self.ca_id)

    @parameterized.expand(
        [
            (None, status.HTTP_401_UNAUTHORIZED),
            ("cert_owner", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
        ]
    )
    def test_get_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(self.cert_owner)
        self.create_certificate(self.testcertificate)
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
        response = self.client.post(self.url, self.testcertificate, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)
