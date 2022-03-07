from tabulate import tabulate

from medperf.ui.ui import UI
from medperf.comms.comms import Comms
from medperf.entities.result import Result


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
                True,
            ]
            for result in results
        ]
        local_uids = [result.uid for result in results]

        # Get remote results data
        remote_results = comms.get_user_results()
        remote_results_data = [
            [result["benchmark"], result["model"], result["dataset"], True, False]
            for result in remote_results
            if result["id"] not in local_uids
        ]
        tab = tabulate(results_data, headers=headers)
        ui.print(tab)
