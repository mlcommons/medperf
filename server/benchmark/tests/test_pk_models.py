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
        mlcube1_owner = "mlcube1_owner"
        mlcube2_owner = "mlcube2_owner"
        data1_owner = "data1_owner"
        data2_owner = "data2_owner"
        other_user = "other_user"

        self.create_user(bmk_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(mlcube1_owner)
        self.create_user(mlcube2_owner)
        self.create_user(data1_owner)
        self.create_user(data2_owner)
        self.create_user(other_user)

        # create benchmark and mlcubes
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            prep_mlcube_owner, ref_mlcube_owner, eval_mlcube_owner, bmk_owner
        )
        mlcube1 = self.mock_mlcube(
            name="mlcube1", mlcube_hash="mlcube1hash", state="OPERATION"
        )
        mlcube2 = self.mock_mlcube(
            name="mlcube2", mlcube_hash="mlcube2hash", state="OPERATION"
        )
        self.set_credentials(mlcube1_owner)
        mlcube1 = self.create_mlcube(mlcube1).data
        self.set_credentials(mlcube2_owner)
        mlcube2 = self.create_mlcube(mlcube2).data

        # create datasets
        dataset1 = self.mock_dataset(
            prep["id"], generated_uid="dataset1", state="OPERATION"
        )
        dataset2 = self.mock_dataset(
            prep["id"], generated_uid="dataset2", state="OPERATION"
        )
        self.set_credentials(data1_owner)
        dataset1 = self.create_dataset(dataset1).data
        self.set_credentials(data2_owner)
        dataset2 = self.create_dataset(dataset2).data

        # create dataset associations: one approved and one not
        # This is to test then that data1_owner can't see the mlcube associations
        # but data2_owner can
        assoc1 = self.mock_dataset_association(
            benchmark["id"], dataset1["id"], approval_status="PENDING"
        )
        self.create_dataset_association(assoc1, data1_owner, bmk_owner)
        assoc2 = self.mock_dataset_association(
            benchmark["id"], dataset2["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc2, data2_owner, bmk_owner)

        # setup globals
        self.bmk_owner = bmk_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.mlcube1_owner = mlcube1_owner
        self.mlcube2_owner = mlcube2_owner
        self.data1_owner = data1_owner
        self.data2_owner = data2_owner
        self.other_user = other_user
        self.benchmark_id = benchmark["id"]
        self.mlcube1_id = mlcube1["id"]
        self.mlcube2_id = mlcube2["id"]

        self.url = self.api_prefix + "/benchmarks/{0}/models/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "bmk_owner"},
        {"actor": "data2_owner"},
    ]
)
class BenchmarkModelGetListTest(BenchmarkTest):
    """Test module for GET /benchmarks/<pk>/models/ endpoint"""

    def setUp(self):
        super(BenchmarkModelGetListTest, self).setUp()
        self.generic_setup()
        # create two association for mlcube1 (one rejected one approved)
        # and one pending association for mlcube2 (just an arbitrary example)

        assoc = self.mock_mlcube_association(
            self.benchmark_id, self.mlcube1_id, approval_status="REJECTED"
        )
        self.create_mlcube_association(assoc, self.mlcube1_owner, self.bmk_owner)
        assoc = self.mock_mlcube_association(
            self.benchmark_id, self.mlcube1_id, approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube1_owner, self.bmk_owner)

        assoc = self.mock_mlcube_association(
            self.benchmark_id, self.mlcube2_id, approval_status="PENDING"
        )
        self.create_mlcube_association(assoc, self.mlcube2_owner, self.bmk_owner)

        self.visible_fields = ["approval_status", "created_at", "model_mlcube"]
        self.set_credentials(self.actor)

    def test_generic_get_benchmark_models_list(self):
        # Arrange
        url = self.url.format(self.benchmark_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 3, "unexpected number of assocs"
        )
        for assoc in response.data["results"]:
            for key in assoc:
                self.assertIn(key, self.visible_fields, f"{key} shouldn't be visible")


class PermissionTest(BenchmarkTest):
    """Test module for permissions of /benchmarks/{pk}/models/ endpoint
    Non-permitted actions:
        GET: for unauthenticated users
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        # create two association for mlcube1 (one rejected one approved)
        # and one pending association for mlcube2 (just an arbitrary example)

        assoc = self.mock_mlcube_association(
            self.benchmark_id, self.mlcube1_id, approval_status="REJECTED"
        )
        self.create_mlcube_association(assoc, self.mlcube1_owner, self.bmk_owner)
        self.url = self.url.format(self.benchmark_id)
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("mlcube1_owner", status.HTTP_403_FORBIDDEN),
            ("mlcube2_owner", status.HTTP_403_FORBIDDEN),
            ("data1_owner", status.HTTP_403_FORBIDDEN),
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
