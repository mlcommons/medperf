from tabulate import tabulate

from medperf import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms


class BenchmarksList:
    @staticmethod
    def run(all: bool = False, comms: Comms = config.comms, ui: UI = config.ui):
        """Lists all benchmarks created by the user by default.
        Use "all" to display all benchmarks in the platform

        Args:
            all (bool): Display all benchmarks in the platform. Defaults to False.
            comms (Comms, optional): Communications instance. Defaults to config.comms
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        if all:
            benchmarks = comms.get_benchmarks()
        else:
            benchmarks = comms.get_user_benchmarks()
        headers = ["UID", "Name", "Description", "State", "Approval Status"]
        formatted_bmarks = []
        desc_max_len = 20
        for bmark in benchmarks:
            if len(bmark["description"]) > desc_max_len:
                desc = bmark["description"][:22] + "..."
                bmark["description"] == desc
            formatted_bmarks.append(bmark)

        data = [
            [
                bmark["id"],
                bmark["name"],
                bmark["description"],
                bmark["state"],
                bmark["approval_status"],
            ]
            for bmark in formatted_bmarks
        ]
        tab = tabulate(data, headers=headers)
        ui.print(tab)
