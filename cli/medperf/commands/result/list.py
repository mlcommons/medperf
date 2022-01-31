from tabulate import tabulate

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Result


class ResultsList:
    @staticmethod
    def run(comms: Comms, ui: UI):
        """Lists all local datasets
	    """
        results = Result.all(ui)
        headers = ["Benchmark UID", "Model UID", "Data UID", "Submitted", "Local"]
        # Get local results data
        results_data = [
            [
                result.benchmark_uid,
                result.model_uid,
                result.dataset_uid,
                result.uid is not None,
            ]
            for result in results
        ]

        # Get remote results data
        remote_results = comms.get_user_results()
        remote_data = [
            [result["benchmark"], result["model"], result["dataset"],]
            for result in remote_results
        ]
        tab = tabulate(results_data, headers=headers)
        ui.print(tab)
