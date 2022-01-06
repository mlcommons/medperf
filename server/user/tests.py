import string
import random
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class UserTest(TestCase):
    """Test module for users APIs"""

    def setUp(self):
        username = "admin"
        password = "".join(
            random.choice(string.ascii_letters) for m in range(10)
        )
        user = User.objects.create_user(
            username=username,
            password=password,
            is_superuser=True,
        )
        user.save()
        self.client = APIClient()
        response = self.client.post(
            "/auth-token/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

    def test_unauthenticated_user(self):
        client = APIClient()
        response = client.get("/users/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.delete("/users/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.put("/users/1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.post("/users/", {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = client.get("/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_crud_user(self):
        testuser = {
            "username": "testdataowner",
            "email": "testdo@example.com",
            "password": "test",
            "first_name": "testdata",
            "last_name": "owner",
        }

        response = self.client.post("/users/", testuser, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uid = response.data["id"]
        response = self.client.get("/users/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in response.data.items():
            if k in testuser:
                self.assertEqual(testuser[k], v)

        response = self.client.get("/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.delete("/users/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get("/users/{0}/".format(uid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_usernames(self):
        testuser = {
            "username": "testdataowner",
            "email": "testdo@example.com",
            "password": "test",
            "first_name": "testdata",
            "last_name": "owner",
        }

        response = self.client.post("/users/", testuser, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post("/users/", testuser, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_emails(self):
        testuser = {
            "username": "testdataowner",
            "email": "testdo@example.com",
            "password": "test",
            "first_name": "testdata",
            "last_name": "owner",
        }

        response = self.client.post("/users/", testuser, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        testuser = {
            "username": "newdataowner",
            "email": "testdo@example.com",
            "password": "test",
            "first_name": "newtestdata",
            "last_name": "owner",
        }

        response = self.client.post("/users/", testuser, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_user(self):
        invalid_uid = 9999
        response = self.client.get("/users/{0}/".format(invalid_uid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_optional_fields(self):
        pass
