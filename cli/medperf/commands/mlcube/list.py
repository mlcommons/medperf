from tabulate import tabulate

from medperf.ui import UI
from medperf.comms import Comms


class CubesList:
    @staticmethod
    def run(comms: Comms, ui: UI, all: bool = False):
        """Lists all mlcubes created by the user by default.
        Use "all" to display all mlcubes in the platform

        Args:
            comms (Comms): Communications interface
            ui (UI): UI interface
        """
        if all:
            cubes = comms.get_cubes()
        else:
            cubes = comms.get_user_cubes()
        headers = ["MLCube UID", "Name", "State"]
        cubes_data = [[cube["id"], cube["name"], cube["state"]] for cube in cubes]

        tab = tabulate(cubes_data, headers=headers)
        ui.print(tab)
