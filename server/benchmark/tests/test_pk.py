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
        other_user = "other_user"

        self.create_user(bmk_owner)
        self.create_user(prep_mlcube_owner)
        self.create_user(ref_mlcube_owner)
        self.create_user(eval_mlcube_owner)
        self.create_user(other_user)

        # setup globals
        self.bmk_owner = bmk_owner
        self.prep_mlcube_owner = prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.other_user = other_user

        self.url = self.api_prefix + "/benchmarks/{0}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "prep_mlcube_owner"},
        {"actor": "ref_mlcube_owner"},
        {"actor": "eval_mlcube_owner"},
        {"actor": "bmk_owner"},
        {"actor": "other_user"},
    ]
)
class BenchmarkGetTest(BenchmarkTest):
    """Test module for GET /benchmarks/<pk>"""

    def setUp(self):
        super(BenchmarkGetTest, self).setUp()
        self.generic_setup()
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
        )
        self.testbenchmark = testbenchmark
        self.set_credentials(self.actor)

    def test_generic_get_benchmark(self):
        # Arrange
        bmk_id = self.testbenchmark["id"]
        url = self.url.format(bmk_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in self.testbenchmark:
                self.assertEqual(self.testbenchmark[k], v, f"Unexpected value for {k}")

    def test_benchmark_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@parameterized_class(
    [
        {"actor": "bmk_owner"},
    ]
)
class BenchmarkPutTest(BenchmarkTest):
    """Test module for PUT /benchmarks/<pk> without approval_status"""

    def setUp(self):
        super(BenchmarkPutTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_put_modifies_as_expected_in_development(self):
        """All editable fields except approval status. It will
        be tested in permissions testcases"""
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
        )

        new_data_preproc_mlcube = self.mock_mlcube(
            name="new prep", mlcube_hash="new prep"
        )
        new_ref_mlcube = self.mock_mlcube(name="new ref", mlcube_hash="new ref")
        new_eval_mlcube = self.mock_mlcube(name="new eval", mlcube_hash="new eval")
        new_prep_id = self.create_mlcube(new_data_preproc_mlcube).data["id"]
        new_ref_id = self.create_mlcube(new_ref_mlcube).data["id"]
        new_eval_id = self.create_mlcube(new_eval_mlcube).data["id"]

        newtestbenchmark = {
            "name": "newstring",
            "description": "newstring",
            "docs_url": "newstring",
            "demo_dataset_tarball_url": "newstring",
            "demo_dataset_tarball_hash": "newstring",
            "demo_dataset_generated_uid": "newstring",
            "data_preparation_mlcube": new_prep_id,
            "reference_model_mlcube": new_ref_id,
            "data_evaluator_mlcube": new_eval_id,
            "metadata": {"newkey": "newvalue"},
            "state": "OPERATION",
            "is_valid": False,
            "is_active": False,
            "user_metadata": {"newkey2": "newvalue2"},
        }
        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(url, newtestbenchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newtestbenchmark:
                self.assertEqual(newtestbenchmark[k], v, f"{k} was not modified")

    @parameterized.expand([("APPROVED",), ("PENDING",)])
    def test_put_modifies_editable_fields_in_operation(self, benchmark_approval_status):
        """All editable fields except approval status. It will
        be tested in permissions testcases"""

        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status=benchmark_approval_status,
            state="OPERATION",
        )
        url = self.url.format(testbenchmark["id"])

        newtestbenchmark = {
            "is_valid": False,
            "is_active": False,
            "user_metadata": {"newkey": "newval"},
            "demo_dataset_tarball_url": "newstring",
        }
        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(url, newtestbenchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newtestbenchmark:
                self.assertEqual(newtestbenchmark[k], v, f"{k} was not modified")

    @parameterized.expand([("APPROVED",), ("PENDING",)])
    def test_put_does_not_modify_non_editable_fields_in_operation(
        self, benchmark_approval_status
    ):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status=benchmark_approval_status,
            state="OPERATION",
        )

        new_data_preproc_mlcube = self.mock_mlcube(
            name="new prep", mlcube_hash="new prep"
        )
        new_ref_mlcube = self.mock_mlcube(name="new ref", mlcube_hash="new ref")
        new_eval_mlcube = self.mock_mlcube(name="new eval", mlcube_hash="new eval")
        new_prep_id = self.create_mlcube(new_data_preproc_mlcube).data["id"]
        new_ref_id = self.create_mlcube(new_ref_mlcube).data["id"]
        new_eval_id = self.create_mlcube(new_eval_mlcube).data["id"]

        newtestbenchmark = {
            "name": "newstring",
            "description": "newstring",
            "docs_url": "newstring",
            "demo_dataset_tarball_hash": "newstring",
            "demo_dataset_generated_uid": "newstring",
            "data_preparation_mlcube": new_prep_id,
            "reference_model_mlcube": new_ref_id,
            "data_evaluator_mlcube": new_eval_id,
            "metadata": {"newkey": "newvalue"},
            "state": "DEVELOPMENT",
        }

        url = self.url.format(testbenchmark["id"])

        for key in newtestbenchmark:
            # Act
            response = self.client.put(url, {key: newtestbenchmark[key]}, format="json")

            # Assert
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"{key} was modified",
            )

    @parameterized.expand(
        [
            ("DEVELOPMENT", "PENDING"),
            ("OPERATION", "PENDING"),
            ("OPERATION", "APPROVED"),
        ]
    )
    def test_put_does_not_modify_readonly_fields_in_all_states(
        self, state, benchmark_approval_status
    ):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status=benchmark_approval_status,
            state=state,
        )

        newtestbenchmark = {
            "owner": 10,
            "approved_at": "some time",
            "created_at": "some time",
            "modified_at": "some time",
        }
        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(url, newtestbenchmark, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in newtestbenchmark.items():
            self.assertNotEqual(v, response.data[k], f"{k} was modified")

    def test_put_respects_unique_name(self):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="APPROVED",
        )

        _, _, _, newtestbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            prep_mlcube_kwargs={"name": "newprep", "mlcube_hash": "newprephash"},
            ref_mlcube_kwargs={"name": "newref", "mlcube_hash": "newrefhash"},
            eval_mlcube_kwargs={"name": "neweval", "mlcube_hash": "newevalhash"},
            state="DEVELOPMENT",
            name="newname",
        )

        put_body = {"name": testbenchmark["name"]}
        url = self.url.format(newtestbenchmark["id"])

        # Act
        response = self.client.put(url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_marking_as_operation_requires_prep_to_be_operation(self):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
            prep_mlcube_kwargs={"state": "DEVELOPMENT"},
        )

        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(url, {"state": "OPERATION"}, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_marking_as_operation_requires_refmodel_to_be_operation(self):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
            ref_mlcube_kwargs={"state": "DEVELOPMENT"},
        )

        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(url, {"state": "OPERATION"}, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_marking_as_operation_requires_evaluator_to_be_operation(self):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
            eval_mlcube_kwargs={"state": "DEVELOPMENT"},
        )

        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(url, {"state": "OPERATION"}, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class BenchmarkApproveTest(BenchmarkTest):
    """Test module for PUT /benchmarks/<pk> with approval_status field"""

    def setUp(self):
        super(BenchmarkApproveTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    @parameterized.expand(
        [
            ("PENDING", "APPROVED", status.HTTP_200_OK),
            ("PENDING", "REJECTED", status.HTTP_200_OK),
            ("APPROVED", "REJECTED", status.HTTP_200_OK),
            ("APPROVED", "PENDING", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", "PENDING", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", "APPROVED", status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_approval_status_change_in_development(
        self, prev_approval_status, new_approval_status, exp_status_code
    ):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status=prev_approval_status,
            state="DEVELOPMENT",
        )
        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(
            url, {"approval_status": new_approval_status}, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, exp_status_code)

    @parameterized.expand(
        [
            ("PENDING", "APPROVED", status.HTTP_200_OK),
            ("PENDING", "REJECTED", status.HTTP_200_OK),
            ("APPROVED", "REJECTED", status.HTTP_200_OK),
            ("APPROVED", "PENDING", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", "PENDING", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", "APPROVED", status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_approval_status_change_in_operation(
        self, prev_approval_status, new_approval_status, exp_status_code
    ):
        # Arrange
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status=prev_approval_status,
            state="OPERATION",
        )
        url = self.url.format(testbenchmark["id"])

        # Act
        response = self.client.put(
            url, {"approval_status": new_approval_status}, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, exp_status_code)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class BenchmarkDeleteTest(BenchmarkTest):
    """Test module for DELETE /benchmarks/<pk>"""

    def setUp(self):
        super(BenchmarkDeleteTest, self).setUp()
        self.generic_setup()
        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
        )
        self.testbenchmark = testbenchmark
        self.set_credentials(self.actor)

    def test_deletion_works_as_expected(self):
        # Arrange
        url = self.url.format(self.testbenchmark["id"])

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionTest(BenchmarkTest):
    """Test module for permissions of /benchmarks/{pk} endpoint
    Non-permitted actions:
        GET: for unauthenticated users
        DELETE: for all users except admin
        PUT:
            including approval_status: for all users except admin
            not including approval_status: for all users except bmk_owner and admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

        _, _, _, testbenchmark = self.shortcut_create_benchmark(
            self.prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            target_approval_status="PENDING",
            state="DEVELOPMENT",
        )
        self.testbenchmark = testbenchmark
        self.url = self.url.format(self.testbenchmark["id"])

    @parameterized.expand(
        [
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

    @parameterized.expand(
        [
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(self.bmk_owner)

        new_data_preproc_mlcube = self.mock_mlcube(
            name="new prep", mlcube_hash="new prep"
        )
        new_ref_mlcube = self.mock_mlcube(name="new ref", mlcube_hash="new ref")
        new_eval_mlcube = self.mock_mlcube(name="new eval", mlcube_hash="new eval")
        new_prep_id = self.create_mlcube(new_data_preproc_mlcube).data["id"]
        new_ref_id = self.create_mlcube(new_ref_mlcube).data["id"]
        new_eval_id = self.create_mlcube(new_eval_mlcube).data["id"]

        newtestbenchmark = {
            "name": "newstring",
            "description": "newstring",
            "docs_url": "newstring",
            "demo_dataset_tarball_url": "newstring",
            "demo_dataset_tarball_hash": "newstring",
            "demo_dataset_generated_uid": "newstring",
            "data_preparation_mlcube": new_prep_id,
            "reference_model_mlcube": new_ref_id,
            "data_evaluator_mlcube": new_eval_id,
            "metadata": {"newkey": "newvalue"},
            "state": "OPERATION",
            "is_valid": False,
            "is_active": False,
            "user_metadata": {"newkey2": "newvalue2"},
            "owner": 10,
            "approved_at": "some time",
            "created_at": "some time",
            "modified_at": "some time",
        }

        self.set_credentials(user)

        for key in newtestbenchmark:
            # Act
            response = self.client.put(
                self.url, {key: newtestbenchmark[key]}, format="json"
            )

            # Assert
            self.assertEqual(
                response.status_code, expected_status, f"{key} was modified"
            )

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_approval_status_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.put(
            self.url, {"approval_status", "APPROVED"}, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, expected_status)

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_delete_permissions(self, user, expected_status):
        # Arrange
        self.set_credentials(user)

        # Act
        response = self.client.delete(self.url)

        # Assert
        self.assertEqual(response.status_code, expected_status)
