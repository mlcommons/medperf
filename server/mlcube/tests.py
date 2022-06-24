import string
import random
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from medperf.tests import MedPerfTest


class MlCubeTest(MedPerfTest):
    """Test module for MLCube APIs"""

    def setUp(self):
        super(MlCubeTest, self).setUp()

        username = "mlcubeowner"
        password = "".join(random.choice(string.ascii_letters) for m in range(10))
        user = User.objects.create_user(username=username, password=password,)
        user.save()
        self.client = APIClient()
        response = self.client.post(
            "/auth-token/", {"username": username, "password": password}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

    def test_unauthenticated_user(self):
        client = APIClient()
        response = client.get("/mlcubes/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.delete("/mlcubes/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.put("/mlcubes/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.post("/mlcubes/", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.get("/mlcubes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud_user(self):
        testmlcube = {
            "name": "testmlcube",
            "git_mlcube_url": "string",
            "git_parameters_url": "string",
            "tarball_url": "string",
            "tarball_hash": "string",
            "metadata": {"key": "value"},
        }

        response = self.client.post("/mlcubes/", testmlcube, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uid = response.data["id"]
        response = self.client.get("/mlcubes/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in testmlcube:
                self.assertEqual(testmlcube[k], v)

        response = self.client.get("/mlcubes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        newmlcube = {
            "name": "newtestmlcube",
            "git_mlcube_url": "newstring",
            "git_parameters_url": "newstring",
            "tarball_url": "newstring",
            "tarball_hash": "newstring",
            "metadata": {"newkey": "newvalue"},
        }

        response = self.client.put(
            "/mlcubes/{0}/".format(uid), newmlcube, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get("/mlcubes/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newmlcube:
                self.assertEqual(newmlcube[k], v)

        # TODO Revisit when delete permissions are fixed
        # response = self.client.delete("/mlcubes/{0}/".format(uid))
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # response = self.client.get("/mlcubes/{0}/".format(uid))
        # self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_mlcube(self):
        invalid_id = 9999
        response = self.client.get("/mlcubes/{0}/".format(invalid_id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_optional_fields(self):
        pass
