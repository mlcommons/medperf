from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import pretty_error
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark


class DatasetBenchmarkAssociation:
    @staticmethod
    def run(data_uid: str, benchmark_uid: int, comms: Comms, ui: UI):
        """Associates a registered dataset with a benchmark

        Args:
            data_uid (int): UID of the registered dataset to associate
            benchmark_uid (int): UID of the benchmark to associate with
        """
        dset = Dataset(data_uid, ui)
        benchmark = Benchmark.get(benchmark_uid, comms)

        if str(dset.preparation_cube_uid) != str(benchmark.data_preparation):
            pretty_error("The specified dataset wasn't prepared for this benchmark", ui)
        approval = dset.request_association_approval(benchmark, ui)

        if approval:
            ui.print("Generating dataset benchmark association")
            comms.associate_dset(dset.uid, benchmark_uid)
        else:
            pretty_error(
                "Dataset association operation cancelled", ui, add_instructions=False
            )
