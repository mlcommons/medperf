from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class ResultsTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        data_owner = "data_owner"
        model_owner = "model_owner"
        bmk_owner = "bmk_owner"
        bmk_prep_mlcube_owner = "bmk_prep_mlcube_owner"
        ref_model_owner = "ref_model_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        other_user = "other_user"

        self.create_user(data_owner)
        self.create_user(model_owner)
        self.create_user(bmk_owner)
        self.create_user(bmk_prep_mlcube_owner)
        self.create_user(ref_model_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(other_user)

        # setup globals
        self.data_owner = data_owner
        self.model_owner = model_owner
        self.bmk_owner = bmk_owner
        self.bmk_prep_mlcube_owner = bmk_prep_mlcube_owner
        self.ref_model_owner = ref_model_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.other_user = other_user

        self.url = self.api_prefix + "/results/"
        self.set_credentials(None)

    def confidential_setup(self, topology="end_to_end_script", asset_url="local"):
        """A benchmark whose script computes the metrics inside a confidential
        VM, over a model whose weights are not public.

        Both are what make an execution's result attested, and so submittable by
        somebody other than the dataset owner. The arguments exist so a test can
        take one of them away."""
        self.set_credentials(self.bmk_prep_mlcube_owner)
        prep = self.create_mlcube(
            self.mock_mlcube(
                name="ccprep",
                container_config={"ccprep": "ccprep"},
                state="OPERATION",
            )
        ).data

        self.set_credentials(self.ref_model_owner)
        ref_model = self.create_model(
            self.mock_asset_model(name="cc_ref_model", state="OPERATION")
        ).data

        self.set_credentials(self.eval_mlcube_owner)
        # Every topology but end_to_end_script scores the predictions in a
        # container of its own.
        evaluator = None
        if topology != "end_to_end_script":
            evaluator = self.create_mlcube(
                self.mock_mlcube(
                    name="cceval",
                    container_config={"cceval": "cceval"},
                    state="OPERATION",
                )
            ).data["id"]

        self.set_credentials(self.bmk_owner)
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
                evaluator,
                name="ccbenchmark",
                topology=topology,
                benchmark_script=script["id"],
            )
        ).data

        self.set_credentials(self.data_owner)
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
            self.data_owner,
            self.bmk_owner,
        )

        self.set_credentials(self.model_owner)
        model = self.create_model(
            self.mock_asset_model(
                name="cc_model", state="OPERATION", asset_url=asset_url
            )
        ).data
        self.create_model_association(
            self.mock_model_association(
                benchmark["id"], model["id"], approval_status="APPROVED"
            ),
            self.model_owner,
            self.bmk_owner,
        )

        self.set_credentials(None)
        return benchmark, dataset, model


@parameterized_class(
    [
        {"actor": "data_owner"},
    ],
)
class GenericResultsPostTest(ResultsTest):
    """Test module for POST /results"""

    def setUp(self):
        super(GenericResultsPostTest, self).setUp()
        self.generic_setup()

        # create benchmark
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_model_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )

        # create dataset
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # create dataset assoc
        assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        # create model model
        self.set_credentials(self.model_owner)
        model = self.mock_model(state="OPERATION")
        model = self.create_model(model).data

        # create model assoc
        assoc = self.mock_model_association(
            benchmark["id"], model["id"], approval_status="APPROVED"
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.model_id = model["id"]

        self.set_credentials(self.actor)

    def test_created_result_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )

        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for k, v in response.data.items():
            if k in testresult:
                self.assertEqual(testresult[k], v, f"unexpected value for {k}")

    def test_default_values_are_as_expected(self):
        """Testing the model fields rules"""

        # Arrange
        default_values = {
            "approved_at": None,
            "approval_status": "PENDING",
            "name": "",
            "metadata": {},
            "user_metadata": {},
            "is_valid": True,
        }
        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )

        for key in default_values:
            if key in testresult:
                del testresult[key]

        # Act
        response = self.client.post(self.url, testresult, format="json")

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
            "owner": 55,
            "created_at": "time",
            "modified_at": "time2",
            "approved_at": "time3",
            "approval_status": "APPROVED",
            "finalized": True,
            "finalized_at": "time4",
        }
        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )

        testresult.update(readonly)

        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )


@parameterized_class(
    [
        {"actor": "other_user"},
        {"actor": "data_owner"},
    ],
)
class ConfidentialResultsPostTest(ResultsTest):
    """Test module for POST /results of a confidential end-to-end execution

    Its result comes back attested -- which script ran, on which inputs,
    producing exactly these metrics -- so whoever operated it may report it, and
    the dataset owner no longer has to be the party holding the CLI.
    """

    def setUp(self):
        super(ConfidentialResultsPostTest, self).setUp()
        self.generic_setup()
        self.benchmark, self.dataset, self.model = self.confidential_setup()
        self.set_credentials(self.actor)

    def test_execution_is_created_and_owned_by_whoever_ran_it(self):
        # Arrange
        testresult = self.mock_result(
            self.benchmark["id"], self.model["id"], self.dataset["id"]
        )

        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.create_user(self.actor)["id"])

    def test_an_unassociated_model_is_still_refused(self):
        """Being allowed to submit is not being allowed to submit anything"""
        # Arrange
        self.set_credentials(self.model_owner)
        unassociated = self.create_model(
            self.mock_asset_model(
                name="unassociated", state="OPERATION", asset_url="local"
            )
        ).data
        self.set_credentials(self.actor)
        testresult = self.mock_result(
            self.benchmark["id"], unassociated["id"], self.dataset["id"]
        )

        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@parameterized_class(
    [
        {"actor": "data_owner"},
    ],
)
class SerializersResultsPostTest(ResultsTest):
    """Test module for serializers rules of POST /results"""

    def setUp(self):
        super(SerializersResultsPostTest, self).setUp()
        self.generic_setup()

        # create benchmark
        prep, ref_model, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_model_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )

        # create dataset
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # create model model
        self.set_credentials(self.model_owner)
        model = self.mock_model(state="OPERATION")
        model = self.create_model(model).data

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.model_id = model["id"]
        self.ref_model_id = ref_model["id"]

        self.set_credentials(self.actor)

    def test_result_creation_with_unassociated_dataset(self):
        # Arrange
        assoc = self.mock_model_association(
            self.bmk_id, self.model_id, approval_status="APPROVED"
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_result_creation_with_unassociated_dataset_and_reference_model(self):
        # Arrange
        testresult = self.mock_result(
            self.bmk_id, self.ref_model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_result_creation_with_unassociated_model(self):
        # Arrange
        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ("PENDING", "PENDING"),
            ("APPROVED", "PENDING"),
            ("REJECTED", "PENDING"),
            ("PENDING", "REJECTED"),
            ("APPROVED", "REJECTED"),
            ("REJECTED", "REJECTED"),
            ("PENDING", "APPROVED"),
            ("APPROVED", "APPROVED"),
            ("REJECTED", "APPROVED"),
        ]
    )
    def test_result_creation_with_created_associations(
        self, dataset_status, model_status
    ):
        # Arrange
        assoc = self.mock_model_association(
            self.bmk_id, self.model_id, approval_status=model_status
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=dataset_status
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        if dataset_status == model_status == "APPROVED":
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST

        self.assertEqual(response.status_code, exp_status)

    def test_result_creation_looks_for_latest_model_assocs(self):
        # Arrange
        assoc = self.mock_model_association(
            self.bmk_id, self.model_id, approval_status="APPROVED"
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        assoc = self.mock_model_association(
            self.bmk_id, self.model_id, approval_status="REJECTED"
        )
        self.create_model_association(
            assoc, self.model_owner, self.bmk_owner, set_status_directly=True
        )

        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_result_creation_looks_for_latest_dataset_assocs(self):
        # Arrange
        assoc = self.mock_model_association(
            self.bmk_id, self.model_id, approval_status="APPROVED"
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="REJECTED"
        )
        self.create_dataset_association(
            assoc, self.data_owner, self.bmk_owner, set_status_directly=True
        )

        testresult = self.mock_result(
            self.bmk_id, self.model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_result_creation_with_ref_model(self):
        # Arrange
        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.ref_model_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ],
)
class GenericResultsGetListTest(ResultsTest):
    """Test module for GET /results"""

    def setUp(self):
        super(GenericResultsGetListTest, self).setUp()
        self.generic_setup()

        # create benchmark
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_model_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )

        # create dataset
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # create dataset assoc
        assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        # create model model
        self.set_credentials(self.model_owner)
        model = self.mock_model(state="OPERATION")
        model = self.create_model(model).data

        # create model assoc
        assoc = self.mock_model_association(
            benchmark["id"], model["id"], approval_status="APPROVED"
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        # create result
        self.set_credentials(self.data_owner)
        result = self.mock_result(
            benchmark["id"], model["id"], dataset["id"], results={"r": 1}
        )
        result = self.create_result(result).data
        self.testresult = result

        self.set_credentials(self.actor)

    def test_generic_get_result_list(self):
        # Arrange
        result_id = self.testresult["id"]

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], result_id)


class PermissionTest(ResultsTest):
    """Test module for permissions of /results endpoint
    Non-permitted actions:
        POST: for all users except data_owner, and admins
        GET: for all users except admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

        # create benchmark
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_model_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )

        # create dataset
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # create dataset assoc
        assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        # create model model
        self.set_credentials(self.model_owner)
        model = self.mock_model(state="OPERATION")
        model = self.create_model(model).data

        # create model assoc
        assoc = self.mock_model_association(
            benchmark["id"], model["id"], approval_status="APPROVED"
        )
        self.create_model_association(assoc, self.model_owner, self.bmk_owner)

        self.set_credentials(self.data_owner)
        result = self.mock_result(
            benchmark["id"], model["id"], dataset["id"], results={"r": 1}
        )

        self.testresult = result

        self.set_credentials(None)

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_model_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("model_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_post_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.post(self.url, self.testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_model_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("model_owner", status.HTTP_403_FORBIDDEN),
            ("data_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(self.data_owner)
        self.create_result(self.testresult)
        self.set_credentials(user)

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand(
        [
            # a topology whose metrics are not computed inside the VM
            ("inference_script", "local"),
            # weights anybody can download are not run confidentially
            ("end_to_end_script", "https://example.com/weights.tar.gz"),
        ]
    )
    def test_post_permissions_when_the_execution_is_not_confidential(
        self, topology, asset_url
    ):
        """Take either half away and the dataset owner is the only one who may
        create an execution, exactly as before"""
        # Arrange
        benchmark, dataset, model = self.confidential_setup(topology, asset_url)
        testresult = self.mock_result(benchmark["id"], model["id"], dataset["id"])
        self.set_credentials(self.other_user)

        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
