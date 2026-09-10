from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class DatasetTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        data_owner = "data_owner"
        other_data_owner = "other_data_owner"
        model_owner = "model_owner"
        bmk_owner = "bmk_owner"
        bmk_prep_mlcube_owner = "bmk_prep_mlcube_owner"
        ref_model_owner = "ref_model_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        committee_user = "committee_user"
        other_user = "other_user"

        self.create_user(data_owner)
        self.create_user(other_data_owner)
        self.create_user(model_owner)
        self.create_user(bmk_owner)
        self.create_user(bmk_prep_mlcube_owner)
        self.create_user(ref_model_owner)
        self.create_user(eval_mlcube_owner)
        committee_user_info = self.create_user(committee_user)
        self.create_user(other_user)

        # a benchmark whose script computes the metrics inside a confidential
        # VM, over weights that are not public. Both are what let somebody
        # other than the dataset owner create an execution on their dataset --
        # the case this listing exists for.
        self.set_credentials(bmk_prep_mlcube_owner)
        prep = self.create_mlcube(
            self.mock_mlcube(
                name="ccprep",
                container_config={"ccprep": "ccprep"},
                state="OPERATION",
            )
        ).data

        self.set_credentials(ref_model_owner)
        ref_model = self.create_model(
            self.mock_asset_model(name="cc_ref_model", state="OPERATION")
        ).data

        self.set_credentials(bmk_owner)
        script = self.create_mlcube(
            self.mock_mlcube(
                name="ccscript",
                container_config={"ccscript": "ccscript"},
                state="OPERATION",
            )
        ).data
        benchmark = self.create_benchmark(
            self.mock_benchmark(
                prep["id"],
                ref_model["id"],
                None,
                name="ccbenchmark",
                topology="end_to_end_script",
                benchmark_script=script["id"],
            )
        ).data

        # two datasets on the same benchmark, owned by different people
        self.set_credentials(data_owner)
        dataset = self.create_dataset(
            self.mock_dataset(
                data_preparation_mlcube=prep["id"],
                state="OPERATION",
                name="ccdataset",
                generated_uid="ccdataset",
            )
        ).data
        self.create_dataset_association(
            self.mock_dataset_association(
                benchmark["id"], dataset["id"], approval_status="APPROVED"
            ),
            data_owner,
            bmk_owner,
        )

        self.set_credentials(other_data_owner)
        other_dataset = self.create_dataset(
            self.mock_dataset(
                data_preparation_mlcube=prep["id"],
                state="OPERATION",
                name="otherccdataset",
                generated_uid="otherccdataset",
            )
        ).data
        self.create_dataset_association(
            self.mock_dataset_association(
                benchmark["id"], other_dataset["id"], approval_status="APPROVED"
            ),
            other_data_owner,
            bmk_owner,
        )

        self.set_credentials(model_owner)
        model = self.create_model(
            self.mock_asset_model(
                name="cc_model", state="OPERATION", asset_url="local"
            )
        ).data
        self.create_model_association(
            self.mock_model_association(
                benchmark["id"], model["id"], approval_status="APPROVED"
            ),
            model_owner,
            bmk_owner,
        )

        # setup globals
        self.data_owner = data_owner
        self.other_data_owner = other_data_owner
        self.model_owner = model_owner
        self.bmk_owner = bmk_owner
        self.bmk_prep_mlcube_owner = bmk_prep_mlcube_owner
        self.ref_model_owner = ref_model_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.committee_user = committee_user
        self.other_user = other_user

        self.bmk_id = benchmark["id"]
        self.prep_id = prep["id"]
        self.dataset_id = dataset["id"]
        self.other_dataset_id = other_dataset["id"]
        self.model_id = model["id"]

        self.url = self.api_prefix + "/datasets/{0}/results/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "api_admin"},
    ]
)
class DatasetResultGetListTest(DatasetTest):
    """Test module for GET /datasets/<pk>/results/ endpoint"""

    def setUp(self):
        super(DatasetResultGetListTest, self).setUp()
        self.generic_setup()

        # one execution the data owner ran themselves, and one somebody else
        # operated on their dataset
        self.set_credentials(self.data_owner)
        self.own_result = self.create_result(
            self.mock_result(
                self.bmk_id, self.model_id, self.dataset_id, name="ownresult"
            )
        ).data
        self.set_credentials(self.model_owner)
        self.operated_result = self.create_result(
            self.mock_result(
                self.bmk_id, self.model_id, self.dataset_id, name="operatedresult"
            )
        ).data

        # an execution on somebody else's dataset, which must not appear
        self.set_credentials(self.other_data_owner)
        self.other_dataset_result = self.create_result(
            self.mock_result(
                self.bmk_id, self.model_id, self.other_dataset_id, name="otherresult"
            )
        ).data

        self.set_credentials(self.actor)

    def test_generic_get_dataset_results_list(self):
        # Arrange
        url = self.url.format(self.dataset_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 2, "unexpected number of results"
        )

    def test_an_execution_operated_by_somebody_else_is_listed(self):
        """The reason this endpoint exists: an execution belongs to whoever ran
        it, so `/me/results/` never shows this one to the dataset's owner"""
        # Arrange
        url = self.url.format(self.dataset_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [result["id"] for result in response.data["results"]]
        self.assertIn(self.operated_result["id"], ids)
        self.assertIn(self.own_result["id"], ids)

    def test_results_of_another_dataset_are_not_listed(self):
        # Arrange
        url = self.url.format(self.dataset_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [result["id"] for result in response.data["results"]]
        self.assertNotIn(self.other_dataset_result["id"], ids)

    def test_a_dataset_with_no_executions_lists_nothing(self):
        # Arrange
        self.set_credentials(self.data_owner)
        empty_dataset = self.create_dataset(
            self.mock_dataset(
                data_preparation_mlcube=self.prep_id,
                state="OPERATION",
                name="emptydataset",
                generated_uid="emptydataset",
            )
        ).data
        self.set_credentials(self.actor)
        url = self.url.format(empty_dataset["id"])

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)


class PermissionTest(DatasetTest):
    """Test module for permissions of /datasets/{pk}/results/ endpoint
    Non-permitted actions:
        GET: for all users except the dataset owner and admin. The benchmark
            owner and its committee read a benchmark's executions through
            /benchmarks/<pk>/results/, not through somebody's dataset.
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.data_owner)
        self.create_result(
            self.mock_result(self.bmk_id, self.model_id, self.dataset_id)
        )
        self.url = self.url.format(self.dataset_id)
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("other_data_owner", status.HTTP_403_FORBIDDEN),
            ("model_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_model_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("committee_user", status.HTTP_403_FORBIDDEN),
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

    def test_get_of_a_nonexistent_dataset(self):
        # Arrange
        # TODO: fixme after refactoring permissions. should be 404
        self.set_credentials(self.data_owner)
        url = self.api_prefix + "/datasets/{0}/results/".format(9999)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
