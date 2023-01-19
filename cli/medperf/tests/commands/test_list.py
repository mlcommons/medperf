import os
import pytest
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.tests.mocks.benchmark import generate_benchmark
from medperf.tests.mocks.cube import generate_cube
from medperf.tests.mocks.dataset import generate_dset
from medperf.tests.mocks.result import generate_result

from medperf.exceptions import InvalidArgumentError


def dset_get(id):
    return Dataset(generate_dset(id=id))


@pytest.fixture(params=[Benchmark, Cube, Dataset, Result])
def EntityClass(request):
    return request.param


@pytest.fixture(params={"uids": ["1", "2", "3"]})
def setup(request, mocker, EntityClass):
    uids = request.param.get("uids", [])
    if EntityClass == Benchmark:
        generate_fn = generate_benchmark
    elif EntityClass == Cube:
        generate_fn = generate_cube
    elif EntityClass == Dataset:
        generate_fn = generate_dset
    elif EntityClass == Result:
        mocker.patch(Dataset.get, side_effect=dset_get)
        generate_fn = generate_result

    generated_entities = [EntityClass(generate_fn(id=id)) for id in uids]
    mocker.patch(EntityClass.all, return_value=generated_entities)

    return request.param


@pytest.mark.parametrize(
    "setup", [{"uids": ["283", "17", "493"]}], indirect=True,
)
class TestRun:
    def test_run_(self, EntityClass, setup):
        # Arrange
        id = setup["remote"][0]

        # Act
        entity = EntityClass.get(id)

        # Assert
        assert entity.todict()["id"] == id

    def test_get_retrieves_entity_local_if_not_on_server(self, EntityClass, setup):
        # Arrange
        id = setup["local"][0]

        # Act
        entity = EntityClass.get(id)

        # Assert
        assert entity.todict()["id"] == id

    def test_get_raises_error_if_nonexistent(self, EntityClass, setup):
        # Arrange
        id = str(19283)

        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            EntityClass.get(id)


@pytest.mark.parametrize(
    "setup", [{"local": ["742"]}], indirect=True,
)
class TestToDict:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["local"][0]

    def test_todict_returns_dict_representation(self, EntityClass):
        # Arrange
        ent = EntityClass.get(self.id)

        # Act
        ent_dict = ent.todict()

        # Assert
        assert type(ent_dict) == dict

    def test_todict_can_recreate_object(self, EntityClass):
        # Arrange
        ent = EntityClass.get(self.id)

        # Act
        ent_dict = ent.todict()
        ent_copy = EntityClass(ent_dict)
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

    def test_upload_adds_to_remote(self, EntityClass, setup):
        # Arrange
        uploaded_entities = setup["uploaded"]
        ent = EntityClass.get(self.id)

        # Act
        ent.upload()

        # Assert
        assert ent.todict() in uploaded_entities

    def test_upload_returns_dict(self, EntityClass):
        # Arrange
        ent = EntityClass.get(self.id)

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
    def test_write_stores_entity_locally(self, EntityClass, setup):
        # Arrange
        id = setup["remote"][0]

        # Act
        ent = EntityClass.get(id)
        stored_path = ent.write()

        # Assert
        assert os.path.exists(stored_path)
