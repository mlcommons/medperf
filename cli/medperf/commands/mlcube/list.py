from tabulate import tabulate

from medperf import config
from medperf.entities.cube import Cube


class CubesList:
    @staticmethod
    def run(local: bool = False, mine: bool = False):
        """Lists all mlcubes created by the user by default.

        Args:
            local (bool, optional): List only local cubes. Defaults to False.
            mine (bool, optional): List only cubes owned by the current user. Defaults to False
        """
        comms = config.comms
        ui = config.ui
        cubes = Cube.all(local_only=local, mine_only=mine)
        headers = ["MLCube UID", "Name", "State"]
        cubes_data = [[cube["id"], cube["name"], cube["state"]] for cube in cubes]

        tab = tabulate(cubes_data, headers=headers)
        ui.print(tab)
