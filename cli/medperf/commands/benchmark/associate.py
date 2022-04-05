from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import pretty_error


class AssociateBenchmark:
    @classmethod
    def run(
        cls, benchmark_uid: str, model_uid: str, dset_uid: str, comms: Comms, ui: UI
    ):
        """Associates a dataset or model to the given benchmark

        Args:
            benchmark_uid (str): UID of benchmark to associate entities with
            model_uid (str): UID of model to associate with benchmark
            dset_uid (str): UID of dataset to associate with benchmark
            comms (Comms): _description_
            ui (UI): _description_
        """
        if model_uid and dset_uid:
            pretty_error(
                "Can only associate one entity at a time. Pass a model or a dataset only",
                ui,
            )
        if model_uid is not None:
            comms.associate_cube(model_uid, benchmark_uid)
            ui.print("Association request to MLCube created")

        if dset_uid is not None:
            comms.associate_dset(dset_uid, benchmark_uid)
            ui.print("Association request to dataset created")

