from tabulate import tabulate

from medperf.entities import Dataset
from medperf.ui import UI


class Datasets:
    @staticmethod
    def run(ui: UI):
        """Lists all local datasets
	    """
        dsets = Dataset.all(ui)
        headers = ["UID", "Name", "Data Preparation Cube UID", "Registered"]
        dsets_data = [
            [
                dset.generated_uid,
                dset.name,
                dset.preparation_cube_uid,
                dset.uid is not None,
            ]
            for dset in dsets
        ]
        tab = tabulate(dsets_data, headers=headers)
        ui.print(tab)
