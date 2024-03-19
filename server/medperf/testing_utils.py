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


def setup_api_admin(username):
    token, user_info = create_user(username)
    user_id = user_info["id"]
    set_user_as_admin(user_id)
    return token


def mock_mlcube(**kwargs):
    data = {
        "name": "testmlcube",
        "git_mlcube_url": "string",
        "mlcube_hash": "string",
        "git_parameters_url": "string",
        "parameters_hash": "string",
        "image_tarball_url": "",
        "image_tarball_hash": "",
        "image_hash": "string",
        "additional_files_tarball_url": "string",
        "additional_files_tarball_hash": "string",
        "state": "DEVELOPMENT",
        "is_valid": True,
        "metadata": {"key": "value"},
        "user_metadata": {"key2": "value2"},
    }

    for key, val in kwargs.items():
        if key not in data:
            raise ValueError(f"Invalid argument: {key}")
        data[key] = val

    return data


def mock_dataset(data_preparation_mlcube, **kwargs):
    data = {
        "name": "dataset",
        "description": "dataset-sample",
        "location": "string",
        "input_data_hash": "string",
        "generated_uid": "string",
        "split_seed": 0,
        "data_preparation_mlcube": data_preparation_mlcube,
        "is_valid": True,
        "submitted_as_prepared": False,
        "state": "DEVELOPMENT",
        "generated_metadata": {"key": "value"},
        "user_metadata": {"key2": "value2"},
        "report": {"key3": "value3"},
    }

    for key, val in kwargs.items():
        if key not in data:
            raise ValueError(f"Invalid argument: {key}")
        data[key] = val

    return data


def mock_benchmark(
    data_preparation_mlcube,
    reference_model_mlcube,
    data_evaluator_mlcube,
    **kwargs,
):
    data = {
        "name": "string",
        "description": "string",
        "docs_url": "string",
        "demo_dataset_tarball_url": "string",
        "demo_dataset_tarball_hash": "string",
        "demo_dataset_generated_uid": "string",
        "data_preparation_mlcube": data_preparation_mlcube,
        "reference_model_mlcube": reference_model_mlcube,
        "data_evaluator_mlcube": data_evaluator_mlcube,
        "metadata": {"key": "value"},
        "state": "DEVELOPMENT",
        "is_valid": True,
        "is_active": True,
        "user_metadata": {"key2": "value2"},
    }

    for key, val in kwargs.items():
        if key not in data:
            raise ValueError(f"Invalid argument: {key}")
        data[key] = val

    return data


def mock_result(benchmark, model, dataset, **kwargs):
    data = {
        "name": "string",
        "benchmark": benchmark,
        "model": model,
        "dataset": dataset,
        "results": {"key": "value"},
        "metadata": {"key2": "value2"},
        "user_metadata": {"key3": "value3"},
        "approval_status": "PENDING",
        "is_valid": True,
    }

    for key, val in kwargs.items():
        if key not in data:
            raise ValueError(f"Invalid argument: {key}")
        data[key] = val

    return data


def mock_dataset_association(benchmark, dataset, **kwargs):
    data = {
        "dataset": dataset,
        "benchmark": benchmark,
        "metadata": {"key": "value"},
        "approval_status": "PENDING",
    }

    for key, val in kwargs.items():
        if key not in data:
            raise ValueError(f"Invalid argument: {key}")
        data[key] = val

    return data


def mock_mlcube_association(benchmark, mlcube, **kwargs):
    data = {
        "model_mlcube": mlcube,
        "benchmark": benchmark,
        "metadata": {"key": "value"},
        "approval_status": "PENDING",
    }

    for key, val in kwargs.items():
        if key not in data:
            raise ValueError(f"Invalid argument: {key}")
        data[key] = val

    return data
