from rest_framework.test import APIClient
from rest_framework import status
from django.conf import settings

from medperf.tests import MedPerfTest


class UserTest(MedPerfTest):
    """Test module for users APIs"""

    def setUp(self):
        super(UserTest, self).setUp()
        self.api_prefix = "/api/" + settings.SERVER_API_VERSION
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_token)

    def test_unauthenticated_user(self):
        client = APIClient()
        response = client.get(self.api_prefix + "/users/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.delete(self.api_prefix + "/users/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.put(self.api_prefix + "/users/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.get(self.api_prefix + "/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud_user(self):
        testusername = "testdataowner"
        _, userinfo = self.create_user(testusername)

        uid = userinfo["id"]
        response = self.client.get(self.api_prefix + "/users/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["username"], testusername)

        response = self.client.get(self.api_prefix + "/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

        response = self.client.delete(self.api_prefix + "/users/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(self.api_prefix + "/users/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_user(self):
        invalid_uid = 9999
        response = self.client.get(self.api_prefix + "/users/{0}/".format(invalid_uid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_optional_fields(self):
        pass
