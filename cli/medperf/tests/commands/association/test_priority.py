from copy import deepcopy
from medperf.exceptions import InvalidArgumentError
from medperf.tests.mocks.benchmarkmodel import generate_benchmarkmodel
import pytest

from medperf.commands.association.priority import AssociationPriority

TEST_ASSOCIATIONS = [
    generate_benchmarkmodel(priority=0, model_mlcube=1),
    generate_benchmarkmodel(priority=0, model_mlcube=2),
    generate_benchmarkmodel(priority=0, model_mlcube=3),
]


def set_priority_behavior(associations):
    def func(benchmark_uid, mlcube_uid, priority):
        for assoc in associations:
            if assoc["model_mlcube"] == mlcube_uid:
                assoc["priority"] = priority

    return func


def get_benchmark_model_associations_behavior(associations):
    def func(benchmark_uid):
        return associations

    return func


def setup_comms(mocker, comms, associations):
    mocker.patch.object(
        comms,
        "get_benchmark_model_associations",
        side_effect=get_benchmark_model_associations_behavior(associations),
    )
    mocker.patch.object(
        comms,
        "update_benchmark_model_association",
        side_effect=set_priority_behavior(associations),
    )


@pytest.fixture(params={"associations": TEST_ASSOCIATIONS})
def setup(request, mocker, comms):
    associations = request.param.get("associations")
    setup_comms(mocker, comms, associations)
    return request.param


@pytest.mark.parametrize(
    "setup",
    [{"associations": TEST_ASSOCIATIONS}],
    indirect=True,
)
class TestRun:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.assets = setup
        self.associations = setup["associations"]

    @pytest.mark.parametrize("model_uid,priority", [(1, 4)])
    def test_run_modifies_priority(self, model_uid, priority):
        # Arrange
        expected_associations = [
            generate_benchmarkmodel(priority=4, model_mlcube=1),
            generate_benchmarkmodel(priority=0, model_mlcube=2),
            generate_benchmarkmodel(priority=0, model_mlcube=3),
        ]

        # Act
        AssociationPriority.run(1, model_uid, priority)

        # Assert
        assert expected_associations == self.associations

    @pytest.mark.parametrize("model_uid", [(55)])
    def test_run_fails_if_cube_not_associated(self, model_uid):
        # Arrange
        original_assocs = deepcopy(self.associations)
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            AssociationPriority.run(1, model_uid, 1)

        assert original_assocs == self.associations
