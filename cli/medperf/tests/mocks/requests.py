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
    return {
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


def cube_metadata_generator(with_params=False, with_tarball=False):
    """Provides an interface for generating mocked cube_metadata responses,
    with the possibility of changing some of the variables that affect the
    workflow

    Args:
        with_params (bool, optional): Wether the mocked cube has parameters. Defaults to False.
        with_tarball (bool, optional): Wether the mocked cube has a tarball. Defaults to False.

    Returns:
        [type]: [description]
    """
    params = "parameters_url" if with_params else ""
    tarball = "additional_files_tarball_url" if with_tarball else ""
    hash = "tarball_hash" if with_tarball else ""

    def cube_metadata_body(cube_uid):
        return {
            "id": cube_uid,
            "name": "test_cube",
            "git_mlcube_url": "mlcube_url",
            "git_parameters_url": params,
            "additional_files_tarball_url": tarball,
            "tarball_hash": hash,
            "metadata": {},
            "created_at": "timestamp",
            "modified_at": "timestamp",
            "owner": 1,
        }

    return cube_metadata_body
