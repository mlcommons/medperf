from tabulate import tabulate

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Benchmark


class BenchmarksList:
    @staticmethod
    def run(comms: Comms, ui: UI, all: bool = False):
        """Lists all benchmarks created by the user by default.
        Use "all" to display all benchmarks in the platform

        Args:
            comms (Comms): Communications instance
            ui (UI): UI instance
            all (bool): Display all benchmarks in the platform. Defaults to False.
        """
        if all:
            benchmarks = comms.get_benchmarks()
        else:
            benchmarks = comms.get_user_benchmarks()
        headers = ["UID", "Name", "Description", "State"]
        formatted_bmarks = []
        desc_max_len = 20
        for bmark in benchmarks:
            if len(bmark["description"]) > desc_max_len:
                desc = bmark["description"][:22] + "..."
                bmark["description"] == desc
            formatted_bmarks.append(bmark)

        data = [
            [bmark["id"], bmark["name"], bmark["description"], bmark["state"]]
            for bmark in formatted_bmarks
        ]
        tab = tabulate(data, headers=headers)
        ui.print(tab)

