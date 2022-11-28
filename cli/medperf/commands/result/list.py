from tabulate import tabulate

from medperf import config
from medperf.entities.result import Result


class ResultsList:
    @staticmethod
    def run(local: bool = False, mine: bool = False):
        """Lists all local datasets

        Args:
            local (bool, optional): Wether to get all local results only. Defaults to False.
            mine (bool, optional): Wether to get all current-user results only. Defaults to False.
        """
        ui = config.ui
        results = Result.all(local_only=local, mine_only=mine)
        headers = [
            "UID",
            "Benchmark UID",
            "Model UID",
            "Data UID",
            "Submitted",
            "Local",
        ]
        # Get local results data
        results_data = [
            [
                result.uid,
                result.benchmark_uid,
                result.model_uid,
                result.dataset_uid,
                result.uid != result.tmp_uid,
                True,
            ]
            for result in results
        ]

        tab = tabulate(results_data, headers=headers)
        ui.print(tab)
