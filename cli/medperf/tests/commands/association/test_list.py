import pytest

from medperf.commands.association.list import ListAssociations

PATCH_ASSOC = "medperf.commands.association.list.{}"


def test_run_gets_dset_and_cube_associations(mocker, comms, ui):
    # Arrange
    dset_spy = mocker.patch.object(comms, "get_datasets_associations", return_value=[])
    cube_spy = mocker.patch.object(comms, "get_cubes_associations", return_value=[])

    # Act
    ListAssociations.run(comms, ui)

    # Assert
    dset_spy.assert_called_once()
    cube_spy.assert_called_once()


@pytest.mark.parametrize("filter", ["approved", "rejected", "PENDING"])
def test_run_filters_associations_by_filter(mocker, comms, ui, filter):
    # Arrange
    dset_assocs = [
        {"dataset": 1, "benchmark": 1, "initiated_by": 1, "approval_status": "PENDING"},
        {
            "dataset": 2,
            "benchmark": 1,
            "initiated_by": 1,
            "approval_status": "APPROVED",
        },
    ]
    cube_assocs = [
        {
            "model_mlcube": 1,
            "benchmark": 1,
            "initiated_by": 1,
            "approval_status": "REJECTED",
        }
    ]
    mocker.patch.object(comms, "get_datasets_associations", return_value=dset_assocs)
    mocker.patch.object(comms, "get_cubes_associations", return_value=cube_assocs)
    tab_spy = mocker.patch(PATCH_ASSOC.format("tabulate"), return_value="")

    # Act
    ListAssociations.run(comms, ui, filter)

    # Assert
    tab_call = tab_spy.call_args_list[0]
    assocs_data = tab_call[0][0]
    status_set = set([assoc[-1] for assoc in assocs_data])
    assert len(status_set) == 1
    assert filter.upper() in status_set

