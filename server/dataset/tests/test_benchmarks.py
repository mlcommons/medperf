from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class DatasetBenchmarksTest(MedPerfTest):
    def generic_setup(self):
        # setup users
        data_owner = "data_owner"
        bmk_owner = "bmk_owner"
        bmk_prep_mlcube_owner = "bmk_prep_mlcube_owner"
        ref_mlcube_owner = "ref_mlcube_owner"
        eval_mlcube_owner = "eval_mlcube_owner"
        other_user = "other_user"

        self.create_user(data_owner)
        self.create_user(bmk_owner)
        self.create_user(bmk_prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(other_user)

        # setup globals
        self.data_owner = data_owner
        self.bmk_owner = bmk_owner
        self.bmk_prep_mlcube_owner = bmk_prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.other_user = other_user

        self.url = self.api_prefix + "/datasets/benchmarks/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "bmk_owner"},
    ],
)
class GenericDatasetBenchmarksPostTest(DatasetBenchmarksTest):
    """Test module for POST /datasets/benchmarks"""

    def setUp(self):
        super(GenericDatasetBenchmarksPostTest, self).setUp()
        self.generic_setup()
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.set_credentials(self.actor)

    def test_created_association_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        testassoc = self.mock_dataset_association(self.bmk_id, self.dataset_id)

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for k, v in response.data.items():
            if k in testassoc:
                self.assertEqual(testassoc[k], v, f"unexpected value for {k}")

    def test_default_values_are_as_expected(self):
        """Testing the model fields rules"""

        # Arrange
        default_values = {
            "approved_at": None,
            "approval_status": "PENDING",
        }
        testassoc = self.mock_dataset_association(self.bmk_id, self.dataset_id)

        for key in default_values:
            if key in testassoc:
                del testassoc[key]

        # Act
        response = self.client.post(self.url, testassoc, format="json")

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
            "initiated_by": 55,
            "created_at": "time",
            "modified_at": "time2",
            "approved_at": "time3",
        }
        testassoc = self.mock_dataset_association(self.bmk_id, self.dataset_id)

        testassoc.update(readonly)

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "bmk_owner"},
    ]
)
class SerializersDatasetBenchmarksPostTest(DatasetBenchmarksTest):
    """Test module for serializers rules of POST /datasets/benchmarks"""

    def setUp(self):
        super(SerializersDatasetBenchmarksPostTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    @parameterized.expand([("DEVELOPMENT",), ("OPERATION",)])
    def test_association_with_unapproved_benchmark(self, state):
        # Arrange
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state=state,
        )
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )

        self.set_credentials(self.data_owner)
        dataset = self.create_dataset(dataset).data
        self.set_credentials(self.actor)

        testassoc = self.mock_dataset_association(benchmark["id"], dataset["id"])

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_association_failure_with_development_dataset(self):
        # Arrange
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="DEVELOPMENT"
        )

        self.set_credentials(self.data_owner)
        dataset = self.create_dataset(dataset).data
        self.set_credentials(self.actor)

        testassoc = self.mock_dataset_association(benchmark["id"], dataset["id"])

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_association_failure_with_dataset_not_prepared_with_benchmark_prep_cube(
        self,
    ):
        # Arrange
        _, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        prep = self.mock_mlcube(
            name="someprep", mlcube_hash="someprep", state="OPERATION"
        )
        prep = self.create_mlcube(prep).data
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )

        self.set_credentials(self.data_owner)
        dataset = self.create_dataset(dataset).data
        self.set_credentials(self.actor)

        testassoc = self.mock_dataset_association(benchmark["id"], dataset["id"])

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ("PENDING", status.HTTP_201_CREATED),
            ("APPROVED", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_specified_association_approval_status_while_not_having_previous_association(
        self, approval_status, exp_statuscode
    ):
        # Arrange
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )

        self.set_credentials(self.data_owner)
        dataset = self.create_dataset(dataset).data
        self.set_credentials(self.actor)

        testassoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status=approval_status
        )

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(
            response.status_code,
            exp_statuscode,
            f"test failed for approval_status={approval_status}",
        )

    @parameterized.expand(
        [
            ("PENDING", "PENDING", status.HTTP_400_BAD_REQUEST),
            ("PENDING", "APPROVED", status.HTTP_400_BAD_REQUEST),
            ("PENDING", "REJECTED", status.HTTP_400_BAD_REQUEST),
            ("APPROVED", "PENDING", status.HTTP_400_BAD_REQUEST),
            ("APPROVED", "APPROVED", status.HTTP_400_BAD_REQUEST),
            ("APPROVED", "REJECTED", status.HTTP_201_CREATED),
            ("REJECTED", "PENDING", status.HTTP_201_CREATED),
            ("REJECTED", "APPROVED", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", "REJECTED", status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_specified_association_approval_status_while_having_previous_association(
        self, prev_approval_status, new_approval_status, exp_statuscode
    ):
        # Arrange
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )

        self.set_credentials(self.data_owner)
        dataset = self.create_dataset(dataset).data
        self.set_credentials(self.actor)

        prev_assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status=prev_approval_status
        )
        self.create_dataset_association(prev_assoc, self.data_owner, self.bmk_owner)

        new_assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status=new_approval_status
        )

        # Act
        response = self.client.post(self.url, new_assoc, format="json")

        # Assert
        self.assertEqual(
            response.status_code,
            exp_statuscode,
            f"test failed when creating {new_approval_status} association "
            f"with a previous {prev_approval_status} one",
        )

    def test_creation_of_rejected_association_sets_approval_time(self):
        # Arrange
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )

        self.set_credentials(self.data_owner)
        dataset = self.create_dataset(dataset).data
        self.set_credentials(self.actor)

        prev_assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(prev_assoc, self.data_owner, self.bmk_owner)

        new_assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status="REJECTED"
        )

        # Act
        response = self.client.post(self.url, new_assoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["approved_at"], None)

    def test_creation_of_pending_association_by_same_user_is_auto_approved(self):
        # Arrange
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.actor,
        )
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        testassoc = self.mock_dataset_association(benchmark["id"], dataset["id"])

        # Act
        response = self.client.post(self.url, testassoc, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["approval_status"], "APPROVED")
        self.assertNotEqual(response.data["approved_at"], None)


class PermissionTest(DatasetBenchmarksTest):
    """Test module for permissions of /datasets/benchmarks endpoint
    Non-permitted actions: POST for all users except data_owner, bmk_owner, and admins
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

        prep, _, _, benchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
        )
        self.set_credentials(self.data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_post_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(user)
        assoc = self.mock_mlcube_association(self.bmk_id, self.dataset_id)

        # Act
        response = self.client.post(self.url, assoc, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)
