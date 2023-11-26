from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.conf import settings
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from time import time
import jwt


def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=4096, backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


PRIVATE_KEY, PUBLIC_KEY = generate_key_pair()


def generate_test_jwt(username):
    payload = {
        "https://medperf.org/email": f"{username}@example.com",
        "iss": "https://localhost:8000/",
        "sub": username,
        "aud": "https://localhost-unittests/",
        "iat": int(time()),
        "exp": int(time()) + 3600,
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return token


def create_user(username):
    token = generate_test_jwt(username)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    response = client.get("/api/" + settings.SERVER_API_VERSION + "/me/")
    return token, response.data


def set_user_as_admin(user_id):
    UserModel = get_user_model()
    user_obj = UserModel.objects.get(id=user_id)
    user_obj.is_staff = True
    user_obj.is_superuser = True
    user_obj.save()


def setup_api_admin():
    token, user_info = create_user("apiadmin")
    user_id = user_info["id"]
    set_user_as_admin(user_id)
    return token
