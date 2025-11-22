from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class BenchmarkCertificatesTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        bmk_owner = "bmk_owner"
        prep_mlcube_owner = "prep_mlcube_owner"
        ref_mlcube_owner = "ref_mlcube_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        model_owner = "model_owner"
        data_owner1 = "data_owner1"
        data_owner2 = "data_owner2"
        data_owner3 = "data_owner3"
        ca_owner = "ca_owner"
        other_user = "other_user"

        self.create_user(bmk_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(model_owner)
        self.create_user(data_owner1)
        self.create_user(data_owner2)
        self.create_user(data_owner3)
        self.create_user(ca_owner)
        self.create_user(other_user)

        # create benchmark
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            prep_mlcube_owner, ref_mlcube_owner, eval_mlcube_owner, bmk_owner
        )

        # create CA
        self.set_credentials(ca_owner)
        ca = self.mock_ca()
        ca = self.create_ca(ca).data

        # create datasets with approved associations
        self.set_credentials(data_owner1)
        dataset1 = self.mock_dataset(
            data_preparation_mlcube=prep["id"],
            state="OPERATION",
            generated_uid="dataset1",
        )
        dataset1 = self.create_dataset(dataset1).data
        assoc1 = self.mock_dataset_association(
            benchmark["id"], dataset1["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc1, data_owner1, bmk_owner)

        self.set_credentials(data_owner2)
        dataset2 = self.mock_dataset(
            data_preparation_mlcube=prep["id"],
            state="OPERATION",
            generated_uid="dataset2",
        )
        dataset2 = self.create_dataset(dataset2).data
        assoc2 = self.mock_dataset_association(
            benchmark["id"], dataset2["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc2, data_owner2, bmk_owner)

        # create dataset3 with PENDING association (should not be included)
        self.set_credentials(data_owner3)
        dataset3 = self.mock_dataset(
            data_preparation_mlcube=prep["id"],
            state="OPERATION",
            generated_uid="dataset3",
        )
        dataset3 = self.create_dataset(dataset3).data
        assoc3 = self.mock_dataset_association(
            benchmark["id"], dataset3["id"], approval_status="PENDING"
        )
        self.create_dataset_association(assoc3, data_owner3, bmk_owner)

        # create certificates for data owners
        self.set_credentials(data_owner1)
        cert1 = self.mock_certificate(ca=ca["id"], name="cert1")
        cert1 = self.create_certificate(cert1).data

        self.set_credentials(data_owner2)
        cert2 = self.mock_certificate(ca=ca["id"], name="cert2")
        cert2 = self.create_certificate(cert2).data

        self.set_credentials(data_owner3)
        cert3 = self.mock_certificate(ca=ca["id"], name="cert3")
        cert3 = self.create_certificate(cert3).data

        # create model and association for testing IsAssociatedModelOwner permission
        self.set_credentials(model_owner)
        model = self.mock_mlcube(state="OPERATION")
        model = self.create_mlcube(model).data
        assoc_model = self.mock_mlcube_association(
            benchmark["id"], model["id"], approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc_model, model_owner, bmk_owner)

        # setup globals
        self.bmk_owner = bmk_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.model_owner = model_owner
        self.data_owner1 = data_owner1
        self.data_owner2 = data_owner2
        self.data_owner3 = data_owner3
        self.ca_owner = ca_owner
        self.other_user = other_user
        self.benchmark_id = benchmark["id"]
        self.cert1_id = cert1["id"]
        self.cert2_id = cert2["id"]
        self.cert3_id = cert3["id"]
        self.url = self.api_prefix + "/benchmarks/{0}/datasets_certificates/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "model_owner"},
    ]
)
class BenchmarkCertificatesGetTest(BenchmarkCertificatesTest):
    """Test module for GET /benchmarks/<pk>/datasets_certificates/"""

    def setUp(self):
        super(BenchmarkCertificatesGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_get_certificates_from_approved_dataset_owners(self):
        """Testing that only certificates from approved dataset owners are returned"""
        # Arrange
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [cert["id"] for cert in response.data["results"]]

        # Should include certificates from data_owner1 and data_owner2 (approved)
        self.assertIn(self.cert1_id, returned_ids)
        self.assertIn(self.cert2_id, returned_ids)

        # Should NOT include certificate from data_owner3 (pending approval)
        self.assertNotIn(self.cert3_id, returned_ids)

    def test_returns_owner_info_with_certificates(self):
        """Testing that owner information is included in response"""
        # Arrange
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cert in response.data["results"]:
            self.assertIn("owner", cert)
            # Owner should be a nested object with user info, not just an ID
            self.assertIsInstance(cert["owner"], dict)

    def test_only_returns_valid_certificates(self):
        """Testing that only valid certificates are returned"""
        # Arrange - invalidate cert1
        self.set_credentials(self.data_owner1)
        self.client.put(
            self.api_prefix + f"/certificates/{self.cert1_id}/",
            {"is_valid": False},
            format="json",
        )

        self.set_credentials(self.actor)
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [cert["id"] for cert in response.data["results"]]

        # Should NOT include invalidated cert1
        self.assertNotIn(self.cert1_id, returned_ids)

        # Should still include cert2
        self.assertIn(self.cert2_id, returned_ids)

    def test_benchmark_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PermissionTest(BenchmarkCertificatesTest):
    """Test module for permissions of /benchmarks/<pk>/datasets_certificates/ endpoint
    Non-permitted actions:
        GET: for all users except associated model owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("data_owner1", status.HTTP_403_FORBIDDEN),
            ("data_owner2", status.HTTP_403_FORBIDDEN),
            ("data_owner3", status.HTTP_403_FORBIDDEN),
            ("ca_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
