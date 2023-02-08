from tabulate import tabulate

from medperf import config
from medperf.entities.benchmark import Benchmark


class BenchmarksList:
    @staticmethod
    def run(local: bool = False, mine: bool = False):
        """Lists all benchmarks created by the user by default.
        Use "all" to display all benchmarks in the platform

        Args:
            all (bool, optional): Display all local benchmarks. Defaults to False.
            mine (bool, optional): Display all current-user benchmarks. Defaults to False.
        """
        ui = config.ui
        benchmarks = Benchmark.all(local_only=local, mine_only=mine)
        headers = ["UID", "Name", "Description", "State", "Approval Status"]

        data = [
            [
                bmark.id if bmark.id is not None else bmark.generated_uid,
                bmark.name,
                bmark.description,
                bmark.state,
                bmark.approval_status,
            ]
            for bmark in benchmarks
        ]
        tab = tabulate(data, headers=headers)
        ui.print(tab)
