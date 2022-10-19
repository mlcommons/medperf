from medperf.enums import Status


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    @property
    def content(self):
        strings = [f"{k}: {v}" for k, v in self.json_data]
        text = "\n".join(strings)
        return text.encode()


def benchmark_body(benchmark_uid):
    return benchmark_dict(
        {
            "id": benchmark_uid,
            "name": "test",
            "description": "mocked benchmark",
            "docs_url": "mock_docs_url",
            "created_at": "timestamp",
            "modified_at": "timestamp",
            "owner": 1,
            "data_preparation_mlcube": 1,
            "reference_model_mlcube": 2,
            "data_evaluator_mlcube": 3,
        }
    )


def cube_metadata_generator(with_params=False, with_tarball=False, with_image=False):
    """Provides an interface for generating mocked cube_metadata responses,
    with the possibility of changing some of the variables that affect the
    workflow

    Args:
        with_params (bool, optional): Wether the mocked cube has parameters. Defaults to False.
        with_tarball (bool, optional): Wether the mocked cube has a tarball. Defaults to False.
        with_image (bool, optional): Wether the mocked cube has an image. Defaults to False.

    Returns:
        [type]: [description]
    """
    params = "parameters_url" if with_params else ""
    tarball = "additional_files_tarball_url" if with_tarball else ""
    tar_hash = "additional_files_tarball_hash" if with_tarball else ""
    image = "image_tarball_url" if with_image else ""
    img_hash = "image_tarball_hash" if with_image else ""

    def cube_metadata_body(cube_uid):
        return cube_dict(
            {
                "id": cube_uid,
                "name": "test_cube",
                "git_mlcube_url": "mlcube_url",
                "git_parameters_url": params,
                "additional_files_tarball_url": tarball,
                "additional_files_tarball_hash": tar_hash,
                "image_tarball_url": image,
                "image_tarball_hash": img_hash,
                "metadata": {},
                "created_at": "timestamp",
                "modified_at": "timestamp",
                "owner": 1,
                "is_valid": True,
            }
        )

    return cube_metadata_body


def benchmark_dict(kwargs={}):
    json_ = {
        "id": None,
        "name": None,
        "data_preparation_mlcube": None,
        "reference_model_mlcube": None,
        "data_evaluator_mlcube": None,
        "demo_dataset_tarball_url": None,
        "demo_dataset_tarball_hash": None,
        "models": [],  # not in the server (OK)
        "description": None,
        "docs_url": None,
        "created_at": None,
        "modified_at": None,
        "approved_at": None,
        "owner": None,
        "demo_dataset_generated_uid": None,
        "state": "DEVELOPMENT",
        "is_valid": True,
        "is_active": True,
        "approval_status": Status.PENDING.value,
        "metadata": {},
        "user_metadata": {},
    }
    for key, val in kwargs.items():
        json_[key] = val

    return json_


def dataset_dict(kwargs={}):
    json_ = {
        "id": None,
        "name": "",
        "description": None,
        "location": None,
        "data_preparation_mlcube": None,
        "input_data_hash": None,
        "generated_uid": None,
        "split_seed": 0,  # Currently this is not used
        "generated_metadata": {},
        "status": Status.PENDING.value,  # not in the server
        "state": "OPERATION",
        "separate_labels": None,  # not in the server
        "is_valid": True,
        "user_metadata": {},
        "created_at": None,
        "modified_at": None,
        "owner": None,
    }
    for key, val in kwargs.items():
        json_[key] = val

    return json_


def result_dict(kwargs={}):
    json_ = {
        "id": None,
        "name": None,
        "owner": None,
        "benchmark": None,
        "model": None,
        "dataset": None,
        "results": {},
        "metadata": {},
        "approval_status": Status.PENDING.value,
        "approved_at": None,
        "created_at": None,
        "modified_at": None,
    }
    for key, val in kwargs.items():
        json_[key] = val

    return json_


def cube_dict(kwargs={}):
    json_ = {
        "name": "",
        "git_mlcube_url": "",
        "git_parameters_url": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
        "additional_files_tarball_url": "",
        "additional_files_tarball_hash": "",
        "state": "OPERATION",
        "is_valid": True,
        "id": None,
        "owner": None,
        "metadata": {},
        "user_metadata": {},
        "created_at": None,
        "modified_at": None,
    }
    for key, val in kwargs.items():
        json_[key] = val

    return json_
