from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from .testing_utils import (
    PUBLIC_KEY,
    setup_api_admin,
    create_user,
    mock_benchmark,
    mock_dataset,
    mock_mlcube,
    mock_result,
    mock_dataset_association,
    mock_mlcube_association,
)


class MedPerfTest(TestCase):
    """Common settings module for MedPerf APIs"""

    # TODO: for all DELETE tests, we should revisit when we allow users
    # to delete. We should test the effects of model.CASCADE and model.PROTECT
    def setUp(self):
        SIMPLE_JWT = {
            "ALGORITHM": "RS256",
            "AUDIENCE": "https://localhost-unittests/",
            "ISSUER": "https://localhost:8000/",
            "JWK_URL": None,
            "USER_ID_FIELD": "username",
            "USER_ID_CLAIM": "sub",
            "TOKEN_TYPE_CLAIM": None,
            "JTI_CLAIM": None,
            "VERIFYING_KEY": PUBLIC_KEY,
        }

        # Disable SSL Redirect during tests and use custom jwt config
        settings_manager = override_settings(
            SECURE_SSL_REDIRECT=False, SIMPLE_JWT=SIMPLE_JWT
        )
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)

        self.tokens = {}
        self.current_user = None

        self.api_admin = "api_admin"
        admin_token = setup_api_admin(self.api_admin)
        self.tokens[self.api_admin] = admin_token
        self.api_prefix = "/api/" + settings.SERVER_API_VERSION
        self.client = APIClient()
        self.mock_benchmark = mock_benchmark
        self.mock_dataset = mock_dataset
        self.mock_mlcube = mock_mlcube
        self.mock_result = mock_result
        self.mock_dataset_association = mock_dataset_association
        self.mock_mlcube_association = mock_mlcube_association

    def create_user(self, username):
        token, _ = create_user(username)
        self.tokens[username] = token

    def set_credentials(self, username):
        self.current_user = username
        if username is None:
            self.client.credentials()
        else:
            token = self.tokens[username]
            self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def __create_asset(self, data, url):
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def create_benchmark(self, data, target_approval_status="APPROVED"):
        # preserve current credentials
        backup_user = self.current_user

        if target_approval_status != "PENDING":
            data["state"] = "OPERATION"
        response = self.__create_asset(data, self.api_prefix + "/benchmarks/")
        if target_approval_status != "PENDING":
            self.set_credentials(self.api_admin)
            uid = response.data["id"]
            url = self.api_prefix + "/benchmarks/{0}/".format(uid)
            response = self.client.put(
                url, {"approval_status": target_approval_status}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # restore user
        self.set_credentials(backup_user)
        return response

    def create_dataset(self, data):
        return self.__create_asset(data, self.api_prefix + "/datasets/")

    def create_mlcube(self, data):
        return self.__create_asset(data, self.api_prefix + "/mlcubes/")

    def create_result(self, data):
        return self.__create_asset(data, self.api_prefix + "/results/")

    def create_dataset_association(
        self, data, initiating_user, approving_user, set_status_directly=False
    ):
        # preserve current credentials
        backup_user = self.current_user

        self.set_credentials(initiating_user)
        target_approval_status = data["approval_status"]
        if not set_status_directly:
            data["approval_status"] = "PENDING"
        response = self.__create_asset(data, self.api_prefix + "/datasets/benchmarks/")
        if target_approval_status != "PENDING" and not set_status_directly:
            dataset_id = data["dataset"]
            benchmark_id = data["benchmark"]
            url = self.api_prefix + f"/datasets/{dataset_id}/benchmarks/{benchmark_id}/"
            self.set_credentials(approving_user)
            response = self.client.put(
                url, {"approval_status": target_approval_status}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # restore user
        self.set_credentials(backup_user)

        return response

    def create_mlcube_association(
        self, data, initiating_user, approving_user, set_status_directly=False
    ):
        # preserve current credentials
        backup_user = self.current_user

        self.set_credentials(initiating_user)
        target_approval_status = data["approval_status"]
        if not set_status_directly:
            data["approval_status"] = "PENDING"
        response = self.__create_asset(data, self.api_prefix + "/mlcubes/benchmarks/")
        if target_approval_status != "PENDING" and not set_status_directly:
            mlcube_id = data["model_mlcube"]
            benchmark_id = data["benchmark"]
            url = self.api_prefix + f"/mlcubes/{mlcube_id}/benchmarks/{benchmark_id}/"
            self.set_credentials(approving_user)
            response = self.client.put(
                url, {"approval_status": target_approval_status}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # restore user
        self.set_credentials(backup_user)

        return response

    def shortcut_create_benchmark(
        self,
        prep_mlcube_owner,
        ref_mlcube_owner,
        eval_mlcube_owner,
        bmk_owner,
        target_approval_status="APPROVED",
        prep_mlcube_kwargs={},
        ref_mlcube_kwargs={},
        eval_mlcube_kwargs={},
        **kwargs,
    ):
        # preserve current credentials
        backup_user = self.current_user

        # create mlcubes
        self.set_credentials(prep_mlcube_owner)
        prep = self.mock_mlcube(name="prep", mlcube_hash="prep", state="OPERATION")
        prep.update(prep_mlcube_kwargs)
        prep = self.create_mlcube(prep).data

        self.set_credentials(ref_mlcube_owner)
        ref_model = self.mock_mlcube(
            name="ref_model", mlcube_hash="ref_model", state="OPERATION"
        )
        ref_model.update(ref_mlcube_kwargs)
        ref_model = self.create_mlcube(ref_model).data

        self.set_credentials(eval_mlcube_owner)
        eval = self.mock_mlcube(name="eval", mlcube_hash="eval", state="OPERATION")
        eval.update(eval_mlcube_kwargs)
        eval = self.create_mlcube(eval).data

        # create benchmark
        self.set_credentials(bmk_owner)
        benchmark = self.mock_benchmark(
            prep["id"], ref_model["id"], eval["id"], **kwargs
        )
        benchmark = self.create_benchmark(
            benchmark, target_approval_status=target_approval_status
        ).data

        # restore user
        self.set_credentials(backup_user)

        return prep, ref_model, eval, benchmark
