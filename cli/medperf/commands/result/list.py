from tabulate import tabulate

from medperf.ui import UI
from medperf.entities import Result


class ResultsList:
    @staticmethod
    def run(ui: UI):
        """Lists all local datasets
	    """
        results = Result.all(ui)
        headers = ["Benchmark UID", "Model UID", "Data UID", "Submitted"]
        results_data = [
            [
                result.benchmark_uid,
                result.model_uid,
                result.dataset_uid,
                result.uid is not None,
            ]
            for result in results
        ]
        tab = tabulate(results_data, headers=headers)
        ui.print(tab)
