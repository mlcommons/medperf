import string
import random
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from medperf.tests import MedPerfTest


class DatasetTest(MedPerfTest):
    """Test module for Dataset APIs"""

    def setUp(self):
        super(DatasetTest, self).setUp()

        username = "dataowner"
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
        data_preproc_mlcube = {
            "name": "testmlcube",
            "git_mlcube_url": "string",
            "git_parameters_url": "string",
            "image_tarball_url": "string",
            "image_tarball_hash": "string",
            "additional_files_tarball_url": "string",
            "additional_files_tarball_hash": "string",
            "metadata": {"key": "value"},
        }

        response = self.client.post("/mlcubes/", data_preproc_mlcube, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.data_preproc_mlcube_id = response.data["id"]

    def test_unauthenticated_user(self):
        client = APIClient()
        response = client.get("/datasets/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.delete("/datasets/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.put("/datasets/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.post("/datasets/", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.get("/datasets/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud_user(self):
        testdataset = {
            "name": "dataset",
            "description": "dataset-sample",
            "location": "string",
            "input_data_hash": "string",
            "generated_uid": "string",
            "split_seed": 0,
            "metadata": {"key": "value"},
            "data_preparation_mlcube": self.data_preproc_mlcube_id,
        }

        response = self.client.post("/datasets/", testdataset, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uid = response.data["id"]
        response = self.client.get("/datasets/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in testdataset:
                self.assertEqual(testdataset[k], v)

        response = self.client.get("/datasets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        newtestdataset = {
            "name": "newdataset",
            "description": "newdataset-sample",
            "location": "newstring",
            "input_data_hash": "newstring",
            "generated_uid": "newstring",
            "split_seed": 0,
            "metadata": {"newkey": "newvalue"},
            "data_preparation_mlcube": self.data_preproc_mlcube_id,
        }

        response = self.client.put(
            "/datasets/{0}/".format(uid), newtestdataset, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get("/datasets/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in newtestdataset:
                self.assertEqual(newtestdataset[k], v)

        # TODO Revisit when delete permissions are fixed
        # response = self.client.delete("/datasets/{0}/".format(uid))
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # response = self.client.get("/datasets/{0}/".format(uid))
        # self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_dataset(self):
        invalid_id = 9999
        response = self.client.get("/datasets/{0}/".format(invalid_id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_gen_uid(self):
        testdataset = {
            "name": "dataset",
            "description": "dataset-sample",
            "location": "string",
            "input_data_hash": "string",
            "generated_uid": "string",
            "split_seed": 0,
            "is_valid": True,
            "metadata": {"key": "value"},
            "data_preparation_mlcube": self.data_preproc_mlcube_id,
        }

        response = self.client.post("/datasets/", testdataset, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post("/datasets/", testdataset, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_optional_fields(self):
        pass
