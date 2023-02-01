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
from medperf.exceptions import InvalidArgumentError


@pytest.fixture(params=[Benchmark, Cube, Dataset, Result])
def Implementation(request):
    return request.param


@pytest.fixture(
    params={"local": ["1", "2", "3"], "remote": ["4", "5", "6"], "user": ["4"]}
)
def setup(request, mocker, comms, Implementation, fs):
    local_ids = request.param.get("local", [])
    remote_ids = request.param.get("remote", [])
    user_ids = request.param.get("user", [])
    # Have a list that will contain all uploaded entities of the given type
    uploaded = []

    if Implementation == Benchmark:
        setup_fs = setup_benchmark_fs
        setup_comms = setup_benchmark_comms
    elif Implementation == Cube:
        setup_fs = setup_cube_fs
        setup_comms = setup_cube_comms
        setup_cube_comms_downloads(mocker, comms, fs)
        mocker.patch("medperf.entities.cube.untar")
    elif Implementation == Dataset:
        setup_fs = setup_dset_fs
        setup_comms = setup_dset_comms
    elif Implementation == Result:
        setup_fs = setup_result_fs
        setup_comms = setup_result_comms

    setup_fs(local_ids, fs)
    setup_comms(mocker, comms, remote_ids, user_ids, uploaded)
    request.param["uploaded"] = uploaded

    return request.param


@pytest.mark.parametrize(
    "setup",
    [{"local": ["283", "17", "493"], "remote": ["283", "1", "2"], "user": ["2"]}],
    indirect=True,
)
class TestAll:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.ids = setup
        self.local_ids = set(self.ids["local"])
        self.remote_ids = set(self.ids["remote"])
        self.user_ids = set(self.ids["user"])

    def test_all_returns_all_remote_and_local(self, Implementation):
        # Arrange
        all_ids = self.local_ids.union(self.remote_ids)

        # Act
        entities = Implementation.all()

        # Assert
        retrieved_ids = set([e.todict()["id"] for e in entities])
        assert all_ids == retrieved_ids

    def test_all_local_only_returns_all_local(self, Implementation):
        # Act
        entities = Implementation.all(local_only=True)

        # Assert
        retrieved_ids = set([e.todict()["id"] for e in entities])
        assert self.local_ids == retrieved_ids

    def test_all_mine_only_returns_user_and_local_entities(self, Implementation):
        # Arrange
        user_ids = self.user_ids.union(self.local_ids)

        # Act
        entities = Implementation.all(mine_only=True)

        # Assert
        retrieved_ids = set([e.todict()["id"] for e in entities])
        assert user_ids == retrieved_ids


@pytest.mark.parametrize(
    "setup", [{"local": ["78"], "remote": ["479", "42", "7", "1"]}], indirect=True,
)
class TestGet:
    def test_get_retrieves_entity_from_server(self, Implementation, setup):
        # Arrange
        id = setup["remote"][0]

        # Act
        entity = Implementation.get(id)

        # Assert
        assert entity.todict()["id"] == id

    def test_get_retrieves_entity_local_if_not_on_server(self, Implementation, setup):
        # Arrange
        id = setup["local"][0]

        # Act
        entity = Implementation.get(id)

        # Assert
        assert entity.todict()["id"] == id

    def test_get_raises_error_if_nonexistent(self, Implementation, setup):
        # Arrange
        id = str(19283)

        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            Implementation.get(id)


@pytest.mark.parametrize(
    "setup", [{"local": ["742"]}], indirect=True,
)
class TestToDict:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["local"][0]

    def test_todict_returns_dict_representation(self, Implementation):
        # Arrange
        ent = Implementation.get(self.id)

        # Act
        ent_dict = ent.todict()

        # Assert
        assert type(ent_dict) == dict

    def test_todict_can_recreate_object(self, Implementation):
        # Arrange
        ent = Implementation.get(self.id)

        # Act
        ent_dict = ent.todict()
        ent_copy = Implementation(ent_dict)
        ent_copy_dict = ent_copy.todict()

        # Assert
        assert ent_dict == ent_copy_dict


@pytest.mark.parametrize(
    "setup", [{"local": ["36"]}], indirect=True,
)
class TestUpload:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["local"][0]

    def test_upload_adds_to_remote(self, Implementation, setup):
        # Arrange
        uploaded_entities = setup["uploaded"]
        ent = Implementation.get(self.id)

        # Act
        ent.upload()

        # Assert
        assert ent.todict() in uploaded_entities

    def test_upload_returns_dict(self, Implementation):
        # Arrange
        ent = Implementation.get(self.id)

        # Act
        ent_dict = ent.upload()

        # Assert
        assert ent_dict == ent.todict()


@pytest.mark.parametrize(
    "setup",
    [{"remote": ["284"]}, {"remote": ["753"], "local": ["753"]}],
    indirect=True,
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
