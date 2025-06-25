from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class BenchmarkTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        bmk_owner = "bmk_owner"
        prep_mlcube_owner = "prep_mlcube_owner"
        ref_mlcube_owner = "ref_mlcube_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        data1_owner = "data1_owner"
        data2_owner = "data2_owner"
        other_user = "other_user"

        self.create_user(bmk_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(data1_owner)
        self.create_user(data2_owner)
        self.create_user(other_user)

        # create benchmark and datasets
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            prep_mlcube_owner, ref_mlcube_owner, eval_mlcube_owner, bmk_owner
        )
        data1 = self.mock_dataset(
            prep["id"], generated_uid="dataset1", state="OPERATION"
        )
        data2 = self.mock_dataset(
            prep["id"], generated_uid="dataset2", state="OPERATION"
        )

        self.set_credentials(data1_owner)
        data1 = self.create_dataset(data1).data
        self.set_credentials(data2_owner)
        data2 = self.create_dataset(data2).data

        # setup globals
        self.bmk_owner = bmk_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.data1_owner = data1_owner
        self.data2_owner = data2_owner
        self.other_user = other_user
        self.benchmark_id = benchmark["id"]
        self.data1_id = data1["id"]
        self.data2_id = data2["id"]

        self.url = self.api_prefix + "/benchmarks/{0}/participants_info/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "bmk_owner"},
    ]
)
class BenchmarkDatasetGetParticipantsInfoTest(BenchmarkTest):
    """Test module for GET /benchmarks/<pk>/participants_info/ endpoint"""

    def setUp(self):
        super(BenchmarkDatasetGetParticipantsInfoTest, self).setUp()
        self.generic_setup()
        # create two association for data1 (one rejected one approved)
        # and one pending association for data2 (just an arbitrary example)

        assoc = self.mock_dataset_association(
            self.benchmark_id, self.data1_id, approval_status="REJECTED"
        )
        self.create_dataset_association(assoc, self.data1_owner, self.bmk_owner)
        assoc = self.mock_dataset_association(
            self.benchmark_id, self.data1_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data1_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.benchmark_id, self.data2_id, approval_status="PENDING"
        )
        self.create_dataset_association(assoc, self.data2_owner, self.bmk_owner)

        self.visible_fields = ["id", "owner"]
        self.set_credentials(self.actor)

    def test_generic_get_participants_info(self):
        # Arrange
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 1, "unexpected number of entries"
        )
        entry = response.data["results"][0]
        for key in entry:
            self.assertIn(key, self.visible_fields, f"{key} shouldn't be visible")
        self.assertEqual(
            isinstance(entry["owner"], dict), True, "Owner is not serialized"
        )
        self.data1_id
        self.assertEqual(
            self.data1_id, entry["id"], "Dataset ID is not the expected one"
        )


class PermissionTest(BenchmarkTest):
    """Test module for permissions of /benchmarks/{pk}/participants_info/ endpoint
    Non-permitted actions:
        GET: for all users except benchmark owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        # create two association for data1 (one rejected one approved)
        # and one pending association for data2 (just an arbitrary example)

        assoc = self.mock_dataset_association(
            self.benchmark_id, self.data1_id, approval_status="REJECTED"
        )
        self.create_dataset_association(assoc, self.data1_owner, self.bmk_owner)
        self.url = self.url.format(self.benchmark_id)
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("data1_owner", status.HTTP_403_FORBIDDEN),
            ("data2_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
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
