from medperf.ui.interface import UI
from medperf.utils import pretty_error
from medperf.comms.interface import Comms
from medperf.commands.mlcube.associate import AssociateCube
from medperf.commands.dataset.associate import AssociateDataset


class AssociateBenchmark:
    @classmethod
    def run(
        cls,
        benchmark_uid: str,
        model_uid: str,
        data_uid: str,
        comms: Comms,
        ui: UI,
        approved=False,
    ):
        """Associates a dataset or model to the given benchmark

        Args:
            benchmark_uid (str): UID of benchmark to associate entities with
            model_uid (str): UID of model to associate with benchmark
            data_uid (str): UID of dataset to associate with benchmark
            comms (Comms): Instance of Communications interface
            ui (UI): Instance of UI interface
            approved (bool): Skip approval step. Defaults to False
        """
        if model_uid and data_uid:
            pretty_error(
                "Can only associate one entity at a time. Pass a model or a dataset only",
                ui,
            )
        if model_uid is not None:
            AssociateCube.run(model_uid, benchmark_uid, comms, ui, approved=approved)

        if data_uid is not None:
            AssociateDataset.run(data_uid, benchmark_uid, comms, ui, approved=approved)
