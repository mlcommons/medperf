from tabulate import tabulate

from medperf import config
from medperf.entities.dataset import Dataset


class DatasetsList:
    @staticmethod
    def run(all: bool = False):
        """List all local and remote users created by user.
        Use "all" to list all remote datasets in the platform

        Args:
            comms (Comms): Communications instance
            ui (UI): UI instance
            all (bool, optional): List all datasets in the platform. Defaults to False.
        """
        comms = config.comms
        ui = config.ui
        # Get local and remote datasets
        local_dsets = Dataset.all()
        if all:
            remote_dsets = comms.get_datasets()
        else:
            remote_dsets = comms.get_user_datasets()

        local_uids = set([dset.uid for dset in local_dsets])
        remote_uids = set([dset["uid"] for dset in remote_dsets])

        # Build data table
        headers = [
            "UID",
            "Name",
            "Data Preparation Cube UID",
            "Registered",
            "Local",
        ]

        # Get local dsets information
        local_dsets_data = [
            [
                dset.uid,
                dset.name,
                dset.preparation_cube_uid,
                dset.generated_uid in remote_uids,
                True,
            ]
            for dset in local_dsets
        ]

        # Get remote dsets information filtered by local
        remote_dsets_data = [
            [dset["id"], dset["name"], "-", True, False,]
            for dset in remote_dsets
            if dset["id"] not in local_uids
        ]

        # Combine dsets
        dsets_data = local_dsets_data + remote_dsets_data
        tab = tabulate(dsets_data, headers=headers)
        ui.print(tab)
