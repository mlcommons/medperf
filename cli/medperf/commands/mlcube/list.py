from tabulate import tabulate

from medperf import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms


class CubesList:
    @staticmethod
    def run(all: bool = False, comms: Comms = config.comms, ui: UI = config.ui):
        """Lists all mlcubes created by the user by default.
        Use "all" to display all mlcubes in the platform

        Args:
            all (bool, optional): Wether to get all mlcubes. Defaults to False
            comms (Comms, optional): Communications instance. Defaults to config.comms
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        if all:
            cubes = comms.get_cubes()
        else:
            cubes = comms.get_user_cubes()
        headers = ["MLCube UID", "Name", "State"]
        cubes_data = [[cube["id"], cube["name"], cube["state"]] for cube in cubes]

        tab = tabulate(cubes_data, headers=headers)
        ui.print(tab)
