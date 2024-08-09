import os
import pytest
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.tests.entities.utils import (
    setup_benchmark_fs,
    setup_benchmark_comms,
    setup_cube_fs,
    setup_cube_comms,
    setup_cube_comms_downloads,
    setup_dset_fs,
    setup_dset_comms,
    setup_result_fs,
    setup_result_comms,
)
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError
from medperf.tests.mocks.comms import TestEntityStorage


@pytest.fixture(params=[Benchmark, Cube, Dataset, Result])
def Implementation(request):
    return request.param


@pytest.fixture(autouse=True)
def setup(request, mocker, comms, Implementation, fs):
    local_ids = request.param.get("local", [])
    remote_ids = request.param.get("remote", [])
    user_ids = request.param.get("user", [])
    # Have a list that will contain all uploaded entities of the given type

    if Implementation == Benchmark:
        setup_fs = setup_benchmark_fs
        setup_comms = setup_benchmark_comms
    elif Implementation == Cube:
        setup_fs = setup_cube_fs
        setup_comms = setup_cube_comms
        setup_cube_comms_downloads(mocker, fs)
    elif Implementation == Dataset:
        setup_fs = setup_dset_fs
        setup_comms = setup_dset_comms
    elif Implementation == Result:
        setup_fs = setup_result_fs
        setup_comms = setup_result_comms
    else:
        raise NotImplementedError("Wrong implementation")

    storage = setup_comms(mocker, comms, remote_ids, user_ids)
    setup_fs(local_ids, fs)

    request.param["storage"] = storage

    return request.param


@pytest.mark.parametrize(
    "setup",
    [
        {
            "unregistered": ["e1", "e2"],
            "local": ["e1", "e2", 283],
            "remote": [283, 1, 2],
            "user": [2],
        }
    ],
    indirect=True,
)
class TestAll:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.ids = setup
        self.unregistered_ids = set(self.ids["unregistered"])
        self.local_ids = set(self.ids["local"])
        self.remote_ids = set(self.ids["remote"])
        self.user_ids = set(self.ids["user"])

    def test_all_returns_all_remote_by_default(self, Implementation):
        # Act
        entities = Implementation.all()

        # Assert
        retrieved_ids = set([e.todict()["id"] for e in entities])
        assert self.remote_ids == retrieved_ids

    def test_all_unregistered_returns_all_unregistered(self, Implementation):
        # Act
        entities = Implementation.all(unregistered=True)

        # Assert
        retrieved_ids = set([e.local_id for e in entities])
        assert self.unregistered_ids == retrieved_ids


@pytest.mark.parametrize(
    "setup",
    [
        {
            "unregistered": ["e1", "e2"],
            "local": ["e1", "e2", 479],
            "remote": [479, 42, 7, 1],
        }
    ],
    indirect=True,
)
class TestGet:
    def test_get_retrieves_entity_from_server(self, Implementation, setup):
        # Arrange
        id = setup["remote"][0]

        # Act
        entity = Implementation.get(id)

        # Assert
        assert entity.todict()["id"] == id

    def test_get_raises_error_if_nonexistent(self, Implementation, setup):
        # Arrange
        id = str(19283)

        # Act & Assert
        with pytest.raises(CommunicationRetrievalError):
            Implementation.get(id)


@pytest.mark.parametrize("setup", [{"remote": [742]}], indirect=True)
class TestToDict:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["remote"][0]

    def test_todict_returns_dict_representation(self, Implementation):
        # Arrange
        ent = Implementation.get(self.id)

        # Act
        ent_dict = ent.todict()

        # Assert
        assert isinstance(ent_dict, dict)

    def test_todict_can_recreate_object(self, Implementation):
        # Arrange
        ent = Implementation.get(self.id)

        # Act
        ent_dict = ent.todict()
        ent_copy = Implementation(**ent_dict)
        ent_copy_dict = ent_copy.todict()

        # Assert
        assert ent_dict == ent_copy_dict


@pytest.mark.parametrize(
    "setup",
    [
        {
            "unregistered": ["e1", "e2"],
            "local": ["e1", "e2"],
        }
    ],
    indirect=True,
)
class TestUpload:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["local"][0]

    def test_upload_adds_to_remote(self, Implementation, setup):
        # Arrange
        storage: TestEntityStorage = setup["storage"]
        assert self.id not in storage.storage

        ent = Implementation.get(self.id)

        # Act
        ent.upload()

        # Assert
        assert ent.todict() in storage.uploaded

    def test_upload_returns_dict(self, Implementation):
        # Arrange
        ent = Implementation.get(self.id)

        # Act
        ent_dict = ent.upload()

        # Assert
        real_dict = ent.todict()
        diff = {}
        for k in set(real_dict) | set(ent_dict):
            if real_dict.get(k) != ent_dict.get(k):
                diff[k] = (real_dict.get(k), ent_dict.get(k))
        assert ent_dict == ent.todict(), f"Expected: {ent_dict}\nGot: {real_dict}\nDiff: {diff}"

    def test_upload_fails_for_test_entity(self, Implementation, setup):
        # Arrange
        storage: TestEntityStorage = setup["storage"]
        ent = Implementation.get(self.id)
        ent.for_test = True

        # pre-check
        len_before_test = len(storage.uploaded)
        assert self.id not in storage.storage
        # Act
        with pytest.raises(InvalidArgumentError):
            ent.upload()

        # Assert
        assert self.id not in storage.storage
        assert ent.todict() not in storage.uploaded
        assert len(storage.uploaded) == len_before_test


@pytest.mark.parametrize(
    "setup", [{"remote": [284]}, {"remote": [753], "local": [753]}], indirect=True
)
class TestWrite:
    def test_write_stores_entity_locally(self, Implementation, setup):
        # Arrange
        id = setup["remote"][0]

        # Act
        ent = Implementation.get(id)
        stored_path = ent.write()

        # Assert
        assert os.path.exists(stored_path)
