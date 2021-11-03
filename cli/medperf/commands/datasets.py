import typer
from tabulate import tabulate

from medperf.entities import Dataset
from medperf.ui import UI


class Datasets:
    @staticmethod
    def run(ui: UI):
        """Lists all local datasets
	    """
        dsets = Dataset.all()
        headers = ["UID", "Name", "Data Preparation Cube UID"]
        dsets_data = [
            [dset.data_uid, dset.name, dset.preparation_cube_uid] for dset in dsets
        ]
        tab = tabulate(dsets_data, headers=headers)
        ui.print(tab)
