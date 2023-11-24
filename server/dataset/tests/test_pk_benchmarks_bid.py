from rest_framework import status

from medperf.tests import MedPerfTest

from parameterized import parameterized, parameterized_class


class DatasetTest(MedPerfTest):
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

        # create benchmark and dataset
        self.set_credentials(bmk_owner)
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            bmk_prep_mlcube_owner,
            ref_mlcube_owner,
            eval_mlcube_owner,
            bmk_owner,
        )
        self.set_credentials(data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # setup globals
        self.data_owner = data_owner
        self.bmk_owner = bmk_owner
        self.bmk_prep_mlcube_owner = bmk_prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.other_user = other_user

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.url = self.api_prefix + "/datasets/{0}/benchmarks/{1}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"initiator": "data_owner", "actor": "bmk_owner"},
        {"initiator": "bmk_owner", "actor": "data_owner"},
    ]
)
class BenchmarkDatasetGetTest(DatasetTest):
    """Test module for GET /datasets/<pk>"""

    def setUp(self):
        super(BenchmarkDatasetGetTest, self).setUp()
        self.generic_setup()

        self.url = self.url.format(self.dataset_id, self.bmk_id)
        self.visible_fields = [
            "approval_status",
            "initiated_by",
            "approved_at",
            "created_at",
            "modified_at",
        ]

        if self.initiator == self.data_owner:
            self.approving_user = self.bmk_owner
        else:
            self.approving_user = self.data_owner

        self.set_credentials(self.actor)

    @parameterized.expand([("PENDING",), ("APPROVED",), ("REJECTED",)])
    def test_generic_get_benchmark_dataset(self, approval_status):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=approval_status
        )

        testassoc = self.create_dataset_association(
            testassoc, self.initiator, self.approving_user
        ).data
        if isinstance(testassoc, list):
            testassoc = testassoc[0]

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in testassoc.items():
            if k in self.visible_fields:
                self.assertIn(k, response.data[0])
                self.assertEqual(response.data[0][k], v, f"Unexpected value for {k}")
            else:
                self.assertNotIn(k, response.data[0], f"{k} should not be visible")

    def test_benchmark_dataset_returns_a_list(self):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="REJECTED"
        )

        self.create_dataset_association(testassoc, self.initiator, self.approving_user)

        testassoc2 = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="PENDING"
        )

        self.create_dataset_association(testassoc2, self.initiator, self.approving_user)

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


@parameterized_class(
    [
        {"initiator": "data_owner", "actor": "bmk_owner"},
        {"initiator": "bmk_owner", "actor": "data_owner"},
    ]
)
class DatasetPutTest(DatasetTest):
    """Test module for PUT /datasets/<pk>"""

    def setUp(self):
        super(DatasetPutTest, self).setUp()
        self.generic_setup()
        self.url = self.url.format(self.dataset_id, self.bmk_id)
        if self.initiator == self.data_owner:
            self.approving_user = self.bmk_owner
        else:
            self.approving_user = self.data_owner
        self.set_credentials(self.actor)

    @parameterized.expand([("PENDING",), ("APPROVED",), ("REJECTED",)])
    def test_put_does_not_modify_readonly_fields(self, approval_status):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=approval_status
        )

        self.create_dataset_association(testassoc, self.initiator, self.approving_user)

        put_body = {
            "initiated_by": 55,
            "approved_at": "time",
            "created_at": "time",
            "modified_at": "time",
        }
        # Act
        response = self.client.put(self.url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in put_body.items():
            self.assertNotEqual(v, response.data[0][k], f"{k} was modified")

    @parameterized.expand([("APPROVED",), ("REJECTED",)])
    def test_modifying_approval_status_to_pending_is_not_allowed(
        self, original_approval_status
    ):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=original_approval_status
        )

        testassoc = self.create_dataset_association(
            testassoc, self.initiator, self.approving_user
        ).data
        if isinstance(testassoc, list):
            testassoc = testassoc[0]

        put_body = {
            "approval_status": "PENDING",
        }
        # Act
        response = self.client.put(self.url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ("PENDING", status.HTTP_200_OK),
            ("APPROVED", status.HTTP_400_BAD_REQUEST),
            ("REJECTED", status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_rejecting_an_association_is_allowed_only_if_it_was_pending(
        self, original_approval_status, exp_status
    ):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=original_approval_status
        )

        testassoc = self.create_dataset_association(
            testassoc, self.initiator, self.approving_user
        ).data
        if isinstance(testassoc, list):
            testassoc = testassoc[0]

        put_body = {
            "approval_status": "REJECTED",
        }
        # Act
        response = self.client.put(self.url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, exp_status)

    @parameterized.expand([("APPROVED",), ("REJECTED",)])
    def test_approving_an_association_is_disallowed_if_it_was_not_pending(
        self, original_approval_status
    ):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=original_approval_status
        )

        testassoc = self.create_dataset_association(
            testassoc, self.initiator, self.approving_user
        ).data
        if isinstance(testassoc, list):
            testassoc = testassoc[0]

        put_body = {
            "approval_status": "APPROVED",
        }
        # Act
        response = self.client.put(self.url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approving_an_association_is_allowed_if_user_is_different(self):
        """This is also a permission test"""

        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="PENDING"
        )

        self.create_dataset_association(testassoc, self.initiator, None)

        put_body = {
            "approval_status": "APPROVED",
        }
        # Act
        response = self.client.put(self.url, put_body, format="json")

        # Assert
        if self.initiator == self.actor:
            exp_status = status.HTTP_400_BAD_REQUEST
        else:
            exp_status = status.HTTP_200_OK

        self.assertEqual(response.status_code, exp_status)

    def test_put_works_on_latest_association(self):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="REJECTED"
        )

        self.create_dataset_association(testassoc, self.initiator, self.approving_user)

        testassoc2 = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="PENDING"
        )

        self.create_dataset_association(testassoc2, self.initiator, self.approving_user)

        put_body = {"approval_status": "REJECTED"}
        # this will fail if latest assoc is not pending.
        # so, success of this test implies the PUT acts on testassoc2 (latest)

        # Act
        response = self.client.put(self.url, put_body, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class DatasetDeleteTest(DatasetTest):
    def setUp(self):
        super(DatasetDeleteTest, self).setUp()
        self.generic_setup()
        self.url = self.url.format(self.dataset_id, self.bmk_id)
        self.set_credentials(self.actor)

    def test_deletion_works_as_expected_for_single_assoc(self):
        # Arrange
        testassoc = self.mock_dataset_association(self.bmk_id, self.dataset_id)
        self.create_dataset_association(testassoc, self.data_owner, self.bmk_owner)

        # Act
        response = self.client.delete(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_deletion_works_as_expected_for_multiple_assoc(self):
        # Arrange
        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status="REJECTED"
        )
        self.create_dataset_association(testassoc, self.data_owner, self.bmk_owner)

        testassoc2 = self.mock_dataset_association(self.bmk_id, self.dataset_id)
        self.create_dataset_association(testassoc2, self.data_owner, self.bmk_owner)

        # Act
        response = self.client.delete(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


@parameterized_class(
    [
        {"initiator": "data_owner", "association_status": "PENDING"},
        {"initiator": "bmk_owner", "association_status": "PENDING"},
        {"initiator": "data_owner", "association_status": "REJECTED"},
        {"initiator": "bmk_owner", "association_status": "REJECTED"},
        {"initiator": "data_owner", "association_status": "APPROVED"},
        {"initiator": "bmk_owner", "association_status": "APPROVED"},
    ]
)
class PermissionTest(DatasetTest):
    """Test module for permissions of /datasets/{pk} endpoint
    Non-permitted actions:
        GET: for all users except data owner, bmk_owner and admin
        DELETE: for all users except admin
        PUT: for all users except data owner, bmk_owner and admin
            if approval_status == APPROVED, initiated_user is not allowed
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()

        self.url = self.url.format(self.dataset_id, self.bmk_id)

        if self.initiator == self.data_owner:
            self.approving_user = self.bmk_owner
        else:
            self.approving_user = self.data_owner

        testassoc = self.mock_dataset_association(
            self.bmk_id, self.dataset_id, approval_status=self.association_status
        )

        self.create_dataset_association(testassoc, self.initiator, self.approving_user)

    # TODO: determine for all tests what should be 404 instead of 400 or 403
    @parameterized.expand(
        [
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
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

    @parameterized.expand(
        [
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange

        put_body = {
            "approval_status": "APPROVED",
            "initiated_by": 55,
            "approved_at": "time",
            "created_at": "time",
            "modified_at": "time",
        }
        self.set_credentials(user)

        for key in put_body:
            # Act
            response = self.client.put(self.url, {key: put_body[key]}, format="json")
            # Assert
            self.assertEqual(
                response.status_code,
                expected_status,
                f"{key} was modified",
            )

    def test_put_permissions_for_approval_status(self):
        # Arrange
        if self.association_status != "PENDING":
            # skip cases that will fail and already tested before
            # they are for reasons are other permissions
            return

        put_body = {
            "approval_status": "APPROVED",
        }
        self.set_credentials(self.initiator)

        # Act
        response = self.client.put(self.url, put_body, format="json")
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # TODO: move this check to permission checks in serializers to return 403

    @parameterized.expand(
        [
            ("data_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
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
