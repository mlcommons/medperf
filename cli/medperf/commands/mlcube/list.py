from tabulate import tabulate

from medperf import config


class CubesList:
    @staticmethod
    def run(all: bool = False):
        """Lists all mlcubes created by the user by default.
        Use "all" to display all mlcubes in the platform

        Args:
            all (bool, optional): Wether to get all mlcubes. Defaults to False
        """
        comms = config.comms
        ui = config.ui
        if all:
            cubes = comms.get_cubes()
        else:
            cubes = comms.get_user_cubes()
        headers = ["MLCube UID", "Name", "State"]
        cubes_data = [[cube["id"], cube["name"], cube["state"]] for cube in cubes]

        tab = tabulate(cubes_data, headers=headers)
        ui.print(tab)
