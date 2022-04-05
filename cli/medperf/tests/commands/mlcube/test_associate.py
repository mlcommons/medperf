import pytest

from medperf.tests.utils import rand_l
from medperf.commands.mlcube.associate import AssociateCube


@pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 5))
def test_run_associates_cube_with_comms(mocker, cube_uid, benchmark_uid, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "associate_cube")

    # Act
    AssociateCube.run(cube_uid, benchmark_uid, comms, ui)

    # Assert
    spy.assert_called_once_with(cube_uid, benchmark_uid)
