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

        # create benchmark
        prep, _, _, benchmark = self.shortcut_create_benchmark(
            bmk_prep_mlcube_owner,
            ref_mlcube_owner,
            eval_mlcube_owner,
            bmk_owner,
        )

        # create dataset
        self.set_credentials(data_owner)
        dataset = self.mock_dataset(
            data_preparation_mlcube=prep["id"], state="OPERATION"
        )
        dataset = self.create_dataset(dataset).data

        # create dataset assoc
        assoc = self.mock_dataset_association(
            benchmark["id"], dataset["id"], approval_status="APPROVED"
        )
        self.create_dataset_association(assoc, data_owner, bmk_owner)

        # create model mlcube
        self.set_credentials(mlcube_owner)
        mlcube = self.mock_mlcube(state="OPERATION")
        mlcube = self.create_mlcube(mlcube).data

        # create mlcube assoc
        assoc = self.mock_mlcube_association(
            benchmark["id"], mlcube["id"], approval_status="APPROVED"
        )
        self.create_mlcube_association(assoc, mlcube_owner, bmk_owner)

        # setup globals
        self.data_owner = data_owner
        self.mlcube_owner = mlcube_owner
        self.bmk_owner = bmk_owner
        self.bmk_prep_mlcube_owner = bmk_prep_mlcube_owner
        self.ref_mlcube_owner = ref_mlcube_owner
        self.eval_mlcube_owner = eval_mlcube_owner
        self.other_user = other_user

        self.bmk_id = benchmark["id"]
        self.dataset_id = dataset["id"]
        self.mlcube_id = mlcube["id"]

        self.url = self.api_prefix + "/results/{0}/"
        self.set_credentials(None)


@parameterized_class(
    [
        {"actor": "data_owner"},
        {"actor": "bmk_owner"},
    ]
)
class ResultGetTest(ResultsTest):
    """Test module for GET /results/<pk>"""

    def setUp(self):
        super(ResultGetTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_generic_get_result(self):
        # Arrange
        result = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        self.set_credentials(self.data_owner)
        result = self.create_result(result).data
        self.set_credentials(self.actor)

        url = self.url.format(result["id"])

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in response.data.items():
            if k in result:
                self.assertEqual(result[k], v, f"Unexpected value for {k}")

    def test_result_not_found(self):
        # Arrange
        invalid_id = 9999
        url = self.url.format(invalid_id)

        # Act
        response = self.client.get(url)

        # Assert
        # TODO: fixme after refactoring permissions. should be 404
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class ResultPutTest(ResultsTest):
    """Test module for PUT /results/<pk>"""

    def setUp(self):
        super(ResultPutTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_put_does_not_modify_readonly_fields(self):
        # Arrange
        result = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        self.set_credentials(self.data_owner)
        result = self.create_result(result).data
        self.set_credentials(self.actor)

        newtestresult = {
            "owner": 10,
            "approved_at": "some time",
            "created_at": "some time",
            "modified_at": "some time",
            "benchmark": 44,
            "model": 444,
            "dataset": 55,
            "results": {"new": 111},
        }
        url = self.url.format(result["id"])

        # Act
        response = self.client.put(url, newtestresult, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in newtestresult.items():
            self.assertNotEqual(v, response.data[k], f"{k} was modified")


@parameterized_class(
    [
        {"actor": "api_admin"},
    ]
)
class ResultDeleteTest(ResultsTest):
    """Test module for DELETE /results/<pk>"""

    # TODO: for all DELETE tests, we should revisit when we allow users
    # to delete. We should test the effects of model.CASCADE and model.PROTECT

    def setUp(self):
        super(ResultDeleteTest, self).setUp()
        self.generic_setup()
        self.set_credentials(self.actor)

    def test_deletion_works_as_expected(self):
        # Arrange
        result = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        self.set_credentials(self.data_owner)
        result = self.create_result(result).data
        self.set_credentials(self.actor)

        url = self.url.format(result["id"])

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url)

        # TODO: fixme after refactoring permissions. should just like this:
        # self.assertEqual(response.status_code, status.HTTP_404_FORBIDDEN)
        if self.actor == self.data_owner:
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        else:
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionTest(ResultsTest):
    """Test module for permissions of /results/{pk} endpoint
    Non-permitted actions:
        GET: for all users except bmk_owner, data_owner, and admin
        DELETE: for all users except admin
        PUT: for all users except admin
    """

    def setUp(self):
        super(PermissionTest, self).setUp()
        self.generic_setup()
        result = self.mock_result(
            self.bmk_id, self.mlcube_id, self.dataset_id, results={"r": 1}
        )
        self.set_credentials(self.data_owner)
        result = self.create_result(result).data
        self.url = self.url.format(result["id"])

        self.result = result
        self.set_credentials(None)

    @parameterized.expand(
        [
            ("mlcube_owner", status.HTTP_403_FORBIDDEN),
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
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("data_owner", status.HTTP_403_FORBIDDEN),
            ("bmk_prep_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("ref_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("eval_mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("other_user", status.HTTP_403_FORBIDDEN),
            (None, status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_put_permissions(self, user, expected_status):
        # Arrange

        # create new assets to edit with
        prep, refmodel, _, newbenchmark = self.shortcut_create_benchmark(
            self.bmk_prep_mlcube_owner,
            self.ref_mlcube_owner,
            self.eval_mlcube_owner,
            self.bmk_owner,
            prep_mlcube_kwargs={"name": "newprep", "mlcube_hash": "newprephash"},
            ref_mlcube_kwargs={"name": "newref", "mlcube_hash": "newrefhash"},
            eval_mlcube_kwargs={"name": "neweval", "mlcube_hash": "newevalhash"},
            name="newbmk",
        )
        self.set_credentials(self.data_owner)
        newdataset = self.mock_dataset(prep["id"], generated_uid="newgen")
        newdataset = self.create_dataset(newdataset).data

        newtestresult = {
            "name": "new",
            "owner": 55,
            "benchmark": newbenchmark["id"],
            "model": refmodel["id"],
            "dataset": newdataset["id"],
            "results": {"new": "t"},
            "metadata": {"new": "t"},
            "user_metadata": {"new": "t"},
            "approval_status": "APPROVED",
            "is_valid": False,
            "approved_at": "time",
            "created_at": "time",
            "modified_at": "time",
        }

        self.set_credentials(user)

        for key in newtestresult:
            # Act
            response = self.client.put(
                self.url, {key: newtestresult[key]}, format="json"
            )

            # Assert
            self.assertEqual(
                response.status_code, expected_status, f"{key} was modified"
            )

    @parameterized.expand(
        [
            ("bmk_owner", status.HTTP_403_FORBIDDEN),
            ("mlcube_owner", status.HTTP_403_FORBIDDEN),
            ("data_owner", status.HTTP_403_FORBIDDEN),
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
