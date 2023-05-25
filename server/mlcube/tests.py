import string
import random
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from medperf.tests import MedPerfTest

User = get_user_model()


class MlCubeTest(MedPerfTest):
    """Test module for MLCube APIs"""

    def setUp(self):
        super(MlCubeTest, self).setUp()
        username = "mlcubeowner"
        password = "".join(random.choice(string.ascii_letters) for m in range(10))
        user = User.objects.create_user(username=username, password=password,)
        user.save()
        self.api_prefix = "/api/" + settings.SERVER_API_VERSION
        self.client = APIClient()
        response = self.client.post(
            self.api_prefix + "/auth-token/", {"username": username, "password": password}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

    def test_unauthenticated_user(self):
        client = APIClient()
        response = client.get(self.api_prefix + "/mlcubes/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.delete(self.api_prefix + "/mlcubes/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.put(self.api_prefix + "/mlcubes/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.post(self.api_prefix + "/mlcubes/", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.get(self.api_prefix + "/mlcubes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud_user(self):
        testmlcube = {
            "name": "testmlcube",
            "git_mlcube_url": "string",
            "mlcube_hash": "string",
            "git_parameters_url": "string",
            "parameters_hash": "string",
            "image_tarball_url": "string",
            "image_tarball_hash": "string",
            "additional_files_tarball_url": "string",
            "additional_files_tarball_hash": "string",
            "metadata": {"key": "value"},
        }

        response = self.client.post(self.api_prefix + "/mlcubes/", testmlcube, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uid = response.data["id"]
        response = self.client.get(self.api_prefix + "/mlcubes/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in testmlcube:
                self.assertEqual(testmlcube[k], v)

        response = self.client.get(self.api_prefix + "/mlcubes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        newmlcube = {
            "name": "newtestmlcube",
            "git_mlcube_url": "newstring",
            "git_parameters_url": "newstring",
            "tarball_url": "newstring",
            "tarball_hash": "newstring",
            "metadata": {"newkey": "newvalue"},
        }

        response = self.client.put(
            self.api_prefix + "/mlcubes/{0}/".format(uid), newmlcube, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.api_prefix + "/mlcubes/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newmlcube:
                self.assertEqual(newmlcube[k], v)

        # TODO Revisit when delete permissions are fixed
        # response = self.client.delete(self.api_prefix + "/mlcubes/{0}/".format(uid))
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # response = self.client.get(self.api_prefix + "/mlcubes/{0}/".format(uid))
        # self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_mlcube(self):
        invalid_id = 9999
        response = self.client.get(self.api_prefix + "/mlcubes/{0}/".format(invalid_id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_optional_fields(self):
        pass
