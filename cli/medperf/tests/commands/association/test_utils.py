from medperf.enums import Status
from medperf.exceptions import InvalidArgumentError
import pytest
from medperf.commands.association import utils


@pytest.mark.parametrize("dset_uid", [None, 1])
@pytest.mark.parametrize("mlcube_uid", [None, 1])
@pytest.mark.parametrize("aggregartor_uid", [None, 1])
@pytest.mark.parametrize("ca_uid", [None, 1])
@pytest.mark.parametrize("bmk_uid", [None, 1])
@pytest.mark.parametrize("training_exp_uid", [None, 1])
def test_validate_args_fails_if_invalid_arguments(
    mocker,
    comms,
    ui,
    dset_uid,
    mlcube_uid,
    aggregartor_uid,
    ca_uid,
    bmk_uid,
    training_exp_uid,
):
    # Arrange
    number_of_components_provided = (
        int(dset_uid is not None)
        + int(mlcube_uid is not None)
        + int(ca_uid is not None)
        + int(aggregartor_uid is not None)
    )
    number_of_experiments_provided = int(bmk_uid is not None) + int(
        training_exp_uid is not None
    )
    is_training_component = dset_uid or aggregartor_uid or ca_uid
    is_evaluation_component = dset_uid or mlcube_uid

    should_succeed = (
        number_of_components_provided == 1
        and number_of_experiments_provided == 1
        and (
            (training_exp_uid and is_training_component)
            or (bmk_uid and is_evaluation_component)
        )
    )

    # Act & Assert
    if not should_succeed:
        with pytest.raises(InvalidArgumentError):
            utils.validate_args(
                bmk_uid,
                training_exp_uid,
                dset_uid,
                mlcube_uid,
                aggregartor_uid,
                ca_uid,
                Status.APPROVED.value,
            )
    else:
        utils.validate_args(
            bmk_uid,
            training_exp_uid,
            dset_uid,
            mlcube_uid,
            aggregartor_uid,
            ca_uid,
            Status.APPROVED.value,
        )


@pytest.mark.parametrize(
    "approval_status, should_fail",
    [("some string", True), (Status.APPROVED.value, False)],
)
def test_validate_args_fails_if_invalid_approval_status(
    mocker, comms, ui, approval_status, should_fail
):
    # Act & Assert
    if should_fail:
        with pytest.raises(InvalidArgumentError):
            utils.validate_args(
                1,
                None,
                1,
                None,
                None,
                None,
                approval_status,
            )
    else:
        utils.validate_args(
            1,
            None,
            1,
            None,
            None,
            None,
            approval_status,
        )


def test_1_latest_associations():
    # Arrange
    associations = [
        {"created_at": "2025-04-16 17:38:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:34:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:32:33", "component": 2, "experiment": 2},
    ]
    expected = [associations[0], associations[2]]

    # Act
    result = utils.filter_latest_associations(associations, "experiment", "component")

    # Assert
    # sort them in some way
    assert sorted(result, key=lambda x: (x["component"], x["experiment"])) == sorted(
        expected, key=lambda x: (x["component"], x["experiment"])
    )


def test_2_latest_associations():
    # Arrange
    associations = [
        {"created_at": "2025-04-16 17:34:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:32:33", "component": 1, "experiment": 1},
        {"created_at": "2025-04-16 17:38:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-17 17:32:33", "component": 1, "experiment": 1},
        {"created_at": "2025-04-16 17:32:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:32:33", "component": 1, "experiment": 3},
    ]
    expected = [associations[2], associations[3], associations[5]]

    # Act
    result = utils.filter_latest_associations(associations, "experiment", "component")

    # Assert
    # sort them in some way
    assert sorted(result, key=lambda x: (x["component"], x["experiment"])) == sorted(
        expected, key=lambda x: (x["component"], x["experiment"])
    )


def test_3_latest_associations():
    # Arrange
    associations = []
    expected = []

    # Act
    result = utils.filter_latest_associations(associations, "experiment", "component")

    # Assert
    # sort them in some way
    assert sorted(result, key=lambda x: (x["component"], x["experiment"])) == sorted(
        expected, key=lambda x: (x["component"], x["experiment"])
    )


def test_1_last_component():
    # Arrange
    associations = [
        {"created_at": "2025-04-16 17:38:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:34:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:32:33", "component": 2, "experiment": 2},
    ]
    expected = [associations[0]]

    # Act
    result = utils.get_last_component(associations, "experiment")

    # Assert
    # sort them in some way
    assert sorted(result, key=lambda x: (x["component"], x["experiment"])) == sorted(
        expected, key=lambda x: (x["component"], x["experiment"])
    )


def test_2_last_component():
    # Arrange
    associations = [
        {"created_at": "2025-04-16 17:38:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-16 17:34:33", "component": 1, "experiment": 2},
        {"created_at": "2025-04-17 17:32:33", "component": 2, "experiment": 2},
        {"created_at": "2025-04-16 17:32:33", "component": 2, "experiment": 3},
    ]
    expected = [associations[2], associations[3]]

    # Act
    result = utils.get_last_component(associations, "experiment")

    # Assert
    # sort them in some way
    assert sorted(result, key=lambda x: (x["component"], x["experiment"])) == sorted(
        expected, key=lambda x: (x["component"], x["experiment"])
    )
