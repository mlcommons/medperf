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

        self.create_user(bmk_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)

        # create mlcubes
        self.set_credentials(prep_mlcube_owner)
        prep = self.mock_mlcube(name="prep", mlcube_hash="prep", state="OPERATION")
        prep = self.create_mlcube(prep).data

        self.set_credentials(ref_mlcube_owner)
        ref_model = self.mock_mlcube(
            name="ref_model", mlcube_hash="ref_model", state="OPERATION"
        )
        ref_model = self.create_mlcube(ref_model).data

        self.set_credentials(eval_mlcube_owner)
        eval = self.mock_mlcube(name="eval", mlcube_hash="eval", state="OPERATION")
        eval = self.create_mlcube(eval).data

        # setup globals
        self.bmk_owner = bmk_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner

        self.prep = prep
        self.ref_model = ref_model
        self.eval = eval

        self.url = self.api_prefix + "/benchmarks/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "prep_mlcube_owner"},
        {"actor": "ref_mlcube_owner"},
        {"actor": "eval_mlcube_owner"},
        {"actor": "bmk_owner"},
    ]
)
class BenchmarkPostTest(BenchmarkTest):
    """Test module for POST /benchmarks"""

    # TODO: there is no conditions on creating benchmarks
    #       or approving benchmarks whose mlcubes are not
    #       OPERATIONAL. Heads-up that this should also
    #       be respected when editing
    def setUp(self):
        super(BenchmarkPostTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_created_benchmark_fields_are_saved_as_expected(self):
        """Testing the valid scenario"""
        # Arrange
        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        get_bmk_url = self.api_prefix + "/benchmarks/{0}/"

        # Act
        response = self.client.post(self.url, benchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uid = response.data["id"]
        response = self.client.get(get_bmk_url.format(uid))

        self.assertEqual(
            response.status_code, status.HTTP_200_OK, "benchmark retreival faild"
        )

        for k, v in response.data.items():
            if k in benchmark:
                self.assertEqual(benchmark[k], v, f"Unexpected value for {k}")

    @parameterized.expand([(True,), (False,)])
    def test_creation_of_duplicate_name_gets_rejected(self, different_name):
        """Testing the model fields rules"""
        # Arrange
        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        self.create_benchmark(benchmark)
        if different_name:
            benchmark["name"] = "different name"

        # Act
        response = self.client.post(self.url, benchmark, format="json")

        # Assert
        if different_name:
            exp_status = status.HTTP_201_CREATED
        else:
            exp_status = status.HTTP_400_BAD_REQUEST
        self.assertEqual(response.status_code, exp_status)

    def test_default_values_are_as_expected(self):
        """Testing the model fields rules"""
        # TODO: demo dataset url should be required again

        # Arrange
        default_values = {
            "description": "",
            "docs_url": "",
            "demo_dataset_tarball_url": "",
            "metadata": {},
            "state": "DEVELOPMENT",
            "is_valid": True,
            "is_active": True,
            "approval_status": "PENDING",
            "user_metadata": {},
            "approved_at": None,
        }

        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        for key in default_values:
            if key in benchmark:
                del benchmark[key]

        # Act
        response = self.client.post(self.url, benchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in default_values.items():
            self.assertEqual(
                val, response.data[key], f"Unexpected default value for {key}"
            )

    @parameterized.expand([("PENDING",), ("APPROVED",), ("REJECTED",)])
    def test_creation_of_new_benchmark_while_previous_pending_is_rejected(
        self, approval_status
    ):
        """Testing the serializer rules"""
        # Arrange
        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        self.create_benchmark(benchmark, target_approval_status=approval_status)
        benchmark["name"] = "new name"

        # Act
        response = self.client.post(self.url, benchmark, format="json")

        # Assert
        if approval_status == "PENDING":
            exp_status = status.HTTP_400_BAD_REQUEST
        else:
            exp_status = status.HTTP_201_CREATED

        self.assertEqual(response.status_code, exp_status)

    def test_readonly_fields(self):
        """Testing the serializer rules"""
        # Arrange
        readonly = {
            "owner": 10,
            "approved_at": "some time",
            "created_at": "some time",
            "modified_at": "some time",
            "approval_status": "APPROVED",
        }
        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        benchmark.update(readonly)

        # Act
        response = self.client.post(self.url, benchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key, val in readonly.items():
            self.assertNotEqual(
                val, response.data[key], f"readonly field {key} was modified"
            )


@parameterized_class(
    [
        {"actor": "prep_mlcube_owner"},
        {"actor": "ref_mlcube_owner"},
        {"actor": "eval_mlcube_owner"},
        {"actor": "bmk_owner"},
        {"actor": "other_user"},
    ]
)
class BenchmarkGetListTest(BenchmarkTest):
    """Test module for GET /benchmarks/ endpoint"""

    def setUp(self):
        super(BenchmarkGetListTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.bmk_owner)
        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        benchmark = self.create_benchmark(benchmark).data

        other_user = "other_user"
        self.create_user(other_user)
        self.other_user = other_user

        self.testbenchmark = benchmark
        self.set_credentials(self.actor)

    def test_generic_get_benchmark_list(self):
        # Arrange
        benchmark_id = self.testbenchmark["id"]

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], benchmark_id)


class PermissionTest(BenchmarkTest):
    """Test module for permissions of /benchmarks/ endpoint
    Non-permitted actions: both GET and POST for unauthenticated users."""

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.bmk_owner)
        benchmark = self.mock_benchmark(
            self.prep["id"], self.ref_model["id"], self.eval["id"]
        )
        self.testbenchmark = benchmark

    @parameterized.expand(
        [
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_get_permissions(self, user, exp_status):
        # Arrange
        self.set_credentials(self.bmk_owner)
        self.create_benchmark(self.testbenchmark)
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
        response = self.client.post(self.url, self.testbenchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)
