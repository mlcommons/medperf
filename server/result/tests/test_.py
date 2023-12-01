from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class ResultsTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        data_owner = "data_owner"
        mlcube_owner = "mlcube_owner"
        bmk_owner = "bmk_owner"
        bmk_prep_mlcube_owner = "bmk_prep_mlcube_owner"
        ref_mlcube_owner = "ref_mlcube_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        other_user = "other_user"

        self.create_user(data_owner)
        self.create_user(mlcube_owner)
        self.create_user(bmk_owner)
        self.create_user(bmk_prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(other_user)

        # setup globals
        self.data_owner = data_owner
        self.mlcube_owner = mlcube_owner
        self.bmk_owner = bmk_owner
        self.bmk_prep_mlcube_owner = bmk_prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.other_user = other_user

        self.url = self.api_prefix + "/results/"
        self.set_credentials(None)


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
            self.ref_mlcube_owner,
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

        # create model mlcube
        self.set_credentials(self.mlcube_owner)
        mlcube = self.mock_mlcube(state="OPERATION")
        mlcube = self.create_mlcube(mlcube).data

        # create mlcube assoc
        assoc = self.mock_mlcube_association(
            benchmark["id"], mlcube["id"], approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.mlcube_id = mlcube["id"]

        self.set_credentials(self.actor)

    def test_created_result_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        testresult = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        get_result_url = self.api_prefix + "/results/{0}/"

        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uid = response.data["id"]
        response = self.client.get(get_result_url.format(uid))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "result retrieval failed",
        )

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
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
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
        }
        testresult = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
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
        {"actor": "data_owner"},
    ],
)
class SerializersResultsPostTest(ResultsTest):
    """Test module for serializers rules of POST /results"""

    def setUp(self):
        super(SerializersResultsPostTest, self).setUp()
        self.generic_setup()

        # create benchmark
        prep, ref_mlcube, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )

        # create dataset
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # create model mlcube
        self.set_credentials(self.mlcube_owner)
        mlcube = self.mock_mlcube(state="OPERATION")
        mlcube = self.create_mlcube(mlcube).data

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.mlcube_id = mlcube["id"]
        self.ref_mlcube_id = ref_mlcube["id"]

        self.set_credentials(self.actor)

    def test_result_creation_with_unassociated_dataset(self):
        # Arrange
        assoc = self.mock_mlcube_association(
            self.bmk_id, self.mlcube_id, approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_result_creation_with_unassociated_mlcube(self):
        # Arrange
        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
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
        self, dataset_status, mlcube_status
    ):
        # Arrange
        assoc = self.mock_mlcube_association(
            self.bmk_id, self.mlcube_id, approval_status=mlcube_status
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=dataset_status
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        testresult = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        if dataset_status == mlcube_status == "APPROVED":
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST

        self.assertEqual(response.status_code, exp_status)

    def test_result_creation_looks_for_latest_model_assocs(self):
        # Arrange
        assoc = self.mock_mlcube_association(
            self.bmk_id, self.mlcube_id, approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

        assoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, self.data_owner, self.bmk_owner)

        assoc = self.mock_mlcube_association(
            self.bmk_id, self.mlcube_id, approval_status="REJECTED"
        )
        self.create_mlcube_association(
            assoc, self.mlcube_owner, self.bmk_owner, set_status_directly=True
        )

        testresult = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        # Act
        response = self.client.post(self.url, testresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_result_creation_looks_for_latest_dataset_assocs(self):
        # Arrange
        assoc = self.mock_mlcube_association(
            self.bmk_id, self.mlcube_id, approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

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
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
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
            self.bmk_id, self.ref_mlcube_id, self.dataset_id, results={"r": 1}
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
            self.ref_mlcube_owner,
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

        # create model mlcube
        self.set_credentials(self.mlcube_owner)
        mlcube = self.mock_mlcube(state="OPERATION")
        mlcube = self.create_mlcube(mlcube).data

        # create mlcube assoc
        assoc = self.mock_mlcube_association(
            benchmark["id"], mlcube["id"], approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

        # create result
        self.set_credentials(self.data_owner)
        result = self.mock_result(
            benchmark["id"], mlcube["id"], dataset["id"], results={"r": 1}
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
            self.ref_mlcube_owner,
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

        # create model mlcube
        self.set_credentials(self.mlcube_owner)
        mlcube = self.mock_mlcube(state="OPERATION")
        mlcube = self.create_mlcube(mlcube).data

        # create mlcube assoc
        assoc = self.mock_mlcube_association(
            benchmark["id"], mlcube["id"], approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, self.mlcube_owner, self.bmk_owner)

        self.set_credentials(self.data_owner)
        result = self.mock_result(
            benchmark["id"], mlcube["id"], dataset["id"], results={"r": 1}
        )

        self.testresult = result

        self.set_credentials(None)

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("mlcube_owner", status.HTTP_403_FORBIDDEN),
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
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("mlcube_owner", status.HTTP_403_FORBIDDEN),
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
