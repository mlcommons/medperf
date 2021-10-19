class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


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


def cube_body(cube_uid):
    return {
        "id": cube_uid,
        "name": "test_cube",
        "git_mlcube_url": "mock_git_mlcube_url",
        "git_parameters_url": "mock_git_parameters_url",
        "tarball_url": "mock_tarball_url",
        "tarball_hash": "mock_tarball_hash",
        "metadata": {},
        "created_at": "timestamp",
        "modified_at": "timestamp",
        "owner": 1,
    }

