from medperf.ui.interface import UI
from medperf.comms.interface import Comms


class AssociateCube:
    @classmethod
    def run(cls, cube_uid: str, benchmark_uid: int, comms: Comms, ui: UI):
        """Associates a cube with a given benchmark

        Args:
            cube_uid (str): UID of model MLCube
            benchmark_uid (int): UID of benchmark
            comms (Comms): Communication instance
            ui (UI): UI instance
        """
        with ui.interactive():
            ui.text = "Creating association request"
            comms.associate_cube(cube_uid, benchmark_uid)
        ui.print("Association request created")

