import typer

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark
from medperf.utils import pretty_error


class DatasetBenchmarkAssociation:
    @staticmethod
    def run(data_uid: int, benchmark_uid: int, comms: Comms, ui: UI):
        """Associates a registered dataset with a benchmark

        Args:
            data_uid (int): UID of the registered dataset to associate
            benchmark_uid (int): UID of the benchmark to associate with
        """
        dset = Dataset(data_uid, ui)
        benchmark = Benchmark.get(benchmark_uid, comms)

        if dset.preparation_cube_uid != benchmark.data_preparation:
            pretty_error("The specified dataset wasn't prepared for this benchmark")
        approval = dset.request_association_approval(benchmark, ui)

        if approval:
            ui.print("Generating dataset benchmark association")
            comms.associate_dset_benchmark(data_uid, benchmark_uid)
        else:
            pretty_error(
                "Dataset association operation cancelled", ui, add_instructions=False
            )
