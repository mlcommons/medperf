from tabulate import tabulate

from medperf import config
from medperf.entities.dataset import Dataset


class DatasetsList:
    @staticmethod
    def run(local: bool = False, mine: bool = False):
        """List all local and remote users created by user.

        Args:
            local (bool, optional): List only local datasets. Defaults to False.
            mine (bool, optional): List only datasets owned by the current user. Defaults to False
        """
        ui = config.ui
        # Get local and remote datasets
        dsets = Dataset.all(local_only=local, mine_only=mine)
        # Build data table
        headers = [
            "UID",
            "Name",
            "Data Preparation Cube UID",
            "Registered",
            "Local",
        ]

        # Get local dsets information
        dsets_data = [
            [
                dset.uid if dset.uid is not None else dset.generated_uid,
                dset.name,
                dset.preparation_cube_uid,
                dset.uid is not None,
                True,
            ]
            for dset in dsets
        ]

        tab = tabulate(dsets_data, headers=headers)
        ui.print(tab)
