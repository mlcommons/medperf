from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class BenchmarkModelCertificatesTest(MedPerfTest):
    """The mirror of test_datasets_certificates: here the model owners hold the
    certificates, and it is a data owner who needs to read them."""

    def generic_setup(self):
        # setup users
        bmk_owner = "bmk_owner"
        prep_mlcube_owner = "prep_mlcube_owner"
        ref_model_owner = "ref_model_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        model_owner1 = "model_owner1"
        model_owner2 = "model_owner2"
        model_owner3 = "model_owner3"
        data_owner = "data_owner"
        ca_owner = "ca_owner"
        committee_user = "committee_user"
        other_user = "other_user"

        self.create_user(bmk_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(ref_model_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(model_owner1)
        self.create_user(model_owner2)
        self.create_user(model_owner3)
        self.create_user(data_owner)
        self.create_user(ca_owner)
        committee_user_info = self.create_user(committee_user)
        self.create_user(other_user)

        # create benchmark
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            prep_mlcube_owner,
            ref_model_owner,
            eval_mlcube_owner,
            bmk_owner,
            committee_member_emails=[committee_user_info["email"]],
        )

        # create CA
        self.set_credentials(ca_owner)
        ca = self.create_ca(self.mock_ca()).data

        # create models with approved associations
        self.set_credentials(model_owner1)
        model1 = self.create_model(
            self.mock_model(
                name="model1",
                container_config={"model": "model1"},
                state="OPERATION",
            )
        ).data
        self.create_model_association(
            self.mock_model_association(
                benchmark["id"], model1["id"], approval_status="APPROVED"
            ),
            model_owner1,
            bmk_owner,
        )

        self.set_credentials(model_owner2)
        model2 = self.create_model(
            self.mock_model(
                name="model2",
                container_config={"model": "model2"},
                state="OPERATION",
            )
        ).data
        self.create_model_association(
            self.mock_model_association(
                benchmark["id"], model2["id"], approval_status="APPROVED"
            ),
            model_owner2,
            bmk_owner,
        )

        # model3's association stays PENDING, so it must not be included
        self.set_credentials(model_owner3)
        model3 = self.create_model(
            self.mock_model(
                name="model3",
                container_config={"model": "model3"},
                state="OPERATION",
            )
        ).data
        self.create_model_association(
            self.mock_model_association(
                benchmark["id"], model3["id"], approval_status="PENDING"
            ),
            model_owner3,
            bmk_owner,
        )

        # create certificates for model owners
        self.set_credentials(model_owner1)
        cert1 = self.create_certificate(
            self.mock_certificate(ca=ca["id"], name="cert1")
        ).data

        self.set_credentials(model_owner2)
        cert2 = self.create_certificate(
            self.mock_certificate(ca=ca["id"], name="cert2")
        ).data

        self.set_credentials(model_owner3)
        cert3 = self.create_certificate(
            self.mock_certificate(ca=ca["id"], name="cert3")
        ).data

        # a dataset with an approved association, which is what lets its owner read
        self.set_credentials(data_owner)
        dataset = self.create_dataset(
            self.mock_dataset(
                data_preparation_mlcube=prep["id"],
                state="OPERATION",
                generated_uid="dataset1",
            )
        ).data
        self.create_dataset_association(
            self.mock_dataset_association(
                benchmark["id"], dataset["id"], approval_status="APPROVED"
            ),
            data_owner,
            bmk_owner,
        )

        # setup globals
        self.bmk_owner = bmk_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.ref_model_owner = ref_model_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.model_owner1 = model_owner1
        self.model_owner2 = model_owner2
        self.model_owner3 = model_owner3
        self.data_owner = data_owner
        self.ca_owner = ca_owner
        self.committee_user = committee_user
        self.other_user = other_user
        self.benchmark_id = benchmark["id"]
        self.cert1_id = cert1["id"]
        self.cert2_id = cert2["id"]
        self.cert3_id = cert3["id"]
        self.url = self.api_prefix + "/benchmarks/{0}/models_certificates/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "bmk_owner"},
        {"actor": "committee_user"},
    ]
)
class BenchmarkModelCertificatesGetTest(BenchmarkModelCertificatesTest):
    """Test module for GET /benchmarks/<pk>/models_certificates/"""

    def setUp(self):
        super(BenchmarkModelCertificatesGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_get_certificates_from_approved_model_owners(self):
        """Only owners whose model is approved for this benchmark: a pending
        association has granted nothing yet"""
        # Arrange
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [cert["id"] for cert in response.data["results"]]
        self.assertIn(self.cert1_id, returned_ids)
        self.assertIn(self.cert2_id, returned_ids)
        self.assertNotIn(self.cert3_id, returned_ids)

    def test_returns_owner_info_with_certificates(self):
        """The caller needs to know whose key each one is"""
        # Arrange
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cert in response.data["results"]:
            self.assertIn("owner", cert)
            self.assertIsInstance(cert["owner"], dict)

    def test_only_returns_valid_certificates(self):
        # Arrange
        self.set_credentials(self.model_owner1)
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
        self.assertNotIn(self.cert1_id, returned_ids)
        self.assertIn(self.cert2_id, returned_ids)

    def test_benchmark_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        # TODO: fixme after refactoring permissions. should be 404
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PermissionTest(BenchmarkModelCertificatesTest):
    """Test module for permissions of /benchmarks/<pk>/models_certificates/
    Non-permitted actions:
        GET: for all users except associated dataset owner, benchmark owner,
            committee members, and admin

    A model owner is refused their peers' certificates here: what they may read
    is the dataset owners', through the mirrored endpoint.
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

    @parameterized.expand(
        [
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_model_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("model_owner1", status.HTTP_403_FORBIDDEN),
            ("model_owner2", status.HTTP_403_FORBIDDEN),
            ("model_owner3", status.HTTP_403_FORBIDDEN),
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
