"""Which endpoint a filtered execution listing goes to.

An execution belongs to whoever operated it, so the three listings the server
offers answer different questions and only one of them is right per filter.
Picking the wrong one does not fail -- it returns somebody else's answer.
"""

import pytest

from medperf import config
from medperf.entities.execution import Execution

CURRENT_USER = 7


@pytest.fixture(autouse=True)
def user(mocker):
    mocker.patch(
        "medperf.entities.execution.get_medperf_user_data",
        return_value={"id": CURRENT_USER},
    )


def test_filtering_by_a_dataset_asks_the_dataset_listing(mocker, comms):
    """The one listing that shows a dataset's owner an execution somebody else
    operated on their data"""
    # Arrange
    fn = mocker.patch.object(config.comms, "get_dataset_executions", return_value=[])
    filters = {"dataset": 3}

    # Act
    comms_fn = Execution.remote_prefilter(filters)
    comms_fn(filters=filters)

    # Assert
    fn.assert_called_once_with(3, filters={})
    assert "dataset" not in filters


def test_filtering_by_a_benchmark_asks_the_benchmark_listing(mocker, comms):
    # Arrange
    fn = mocker.patch.object(config.comms, "get_benchmark_executions", return_value=[])
    filters = {"benchmark": 2}

    # Act
    comms_fn = Execution.remote_prefilter(filters)
    comms_fn(filters=filters)

    # Assert
    fn.assert_called_once_with(2, filters={})


def test_filtering_by_the_current_user_asks_their_own_listing(mocker, comms):
    # Arrange
    fn = mocker.patch.object(config.comms, "get_user_executions")
    filters = {"owner": CURRENT_USER}

    # Act
    comms_fn = Execution.remote_prefilter(filters)

    # Assert
    assert comms_fn is fn
    assert "owner" not in filters


def test_filtering_by_another_user_stays_on_the_generic_listing(mocker, comms):
    """Their executions are not this user's to ask for by owner, and the
    server, not the client, is what says so"""
    # Arrange
    fn = mocker.patch.object(config.comms, "get_executions")
    filters = {"owner": CURRENT_USER + 1}

    # Act
    comms_fn = Execution.remote_prefilter(filters)

    # Assert
    assert comms_fn is fn
    assert filters["owner"] == CURRENT_USER + 1


def test_a_benchmark_wins_over_a_dataset_when_both_are_given(mocker, comms):
    """Only one listing can answer, and the benchmark's is the narrower of the
    two -- a dataset takes part in many benchmarks"""
    # Arrange
    benchmark_fn = mocker.patch.object(
        config.comms, "get_benchmark_executions", return_value=[]
    )
    dataset_fn = mocker.patch.object(
        config.comms, "get_dataset_executions", return_value=[]
    )
    filters = {"benchmark": 2, "dataset": 3}

    # Act
    comms_fn = Execution.remote_prefilter(filters)
    comms_fn(filters=filters)

    # Assert
    benchmark_fn.assert_called_once_with(2, filters={"dataset": 3})
    dataset_fn.assert_not_called()


@pytest.mark.parametrize("filters", [{}, {"dataset": None}, {"benchmark": None}])
def test_nothing_to_narrow_by_stays_on_the_generic_listing(mocker, comms, filters):
    # Arrange
    fn = mocker.patch.object(config.comms, "get_executions")

    # Act
    comms_fn = Execution.remote_prefilter(filters)

    # Assert
    assert comms_fn is fn
