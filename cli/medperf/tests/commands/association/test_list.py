from medperf.enums import Status
import pytest

from medperf.commands.association.list import ListAssociations

PATCH_LIST = "medperf.commands.association.list.{}"


def test_run_gets_dset_and_cube_associations(mocker, comms, ui):
    # Arrange
    dset_spy = mocker.patch.object(comms, "get_datasets_associations", return_value=[])
    cube_spy = mocker.patch.object(comms, "get_cubes_associations", return_value=[])

    # Act
    ListAssociations.run()

    # Assert
    dset_spy.assert_called_once()
    cube_spy.assert_called_once()


@pytest.mark.parametrize("filter", ["approved", "rejected", "PENDING"])
def test_run_filters_associations_by_filter(mocker, comms, ui, filter):
    # Arrange
    dset_assocs = [
        {
            "dataset": 1,
            "benchmark": 1,
            "initiated_by": 1,
            "approval_status": Status.PENDING.value,
        },
        {
            "dataset": 2,
            "benchmark": 1,
            "initiated_by": 1,
            "approval_status": Status.APPROVED.value,
        },
    ]
    cube_assocs = [
        {
            "model_mlcube": 1,
            "benchmark": 1,
            "initiated_by": 1,
            "approval_status": Status.REJECTED.value,
            "priority": 2,
        }
    ]
    mocker.patch.object(comms, "get_datasets_associations", return_value=dset_assocs)
    mocker.patch.object(comms, "get_cubes_associations", return_value=cube_assocs)
    tab_spy = mocker.patch(PATCH_LIST.format("tabulate"), return_value="")

    # Act
    ListAssociations.run(filter)

    # Assert
    tab_call = tab_spy.call_args_list[0]
    assocs_data = tab_call[0][0]
    status_set = set([assoc[-2] for assoc in assocs_data])
    assert len(status_set) == 1
    assert filter.upper() in status_set
