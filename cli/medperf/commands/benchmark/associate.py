from medperf.utils import pretty_error
from medperf.commands.mlcube.associate import AssociateCube
from medperf.commands.dataset.associate import AssociateDataset


class AssociateBenchmark:
    @classmethod
    def run(
        cls,
        benchmark_uid: str,
        model_uid: str,
        data_uid: str,
        approved=False,
        force_test=False,
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
        too_many_resources = data_uid and model_uid
        no_resource = data_uid is None and model_uid is None
        if no_resource or too_many_resources:
            pretty_error("Invalid arguments. Must provide either a dataset or mlcube")
        if model_uid is not None:
            AssociateCube.run(
                model_uid, benchmark_uid, approved=approved, force_test=force_test
            )

        if data_uid is not None:
            AssociateDataset.run(
                data_uid, benchmark_uid, approved=approved, force_test=force_test
            )
