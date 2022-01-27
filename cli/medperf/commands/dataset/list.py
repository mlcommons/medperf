from tabulate import tabulate

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset


class DatasetsList:
    @staticmethod
    def run(comms: Comms, ui: UI):
        """Lists all local datasets
	    """
        # Get local and remote datasets
        local_dsets = Dataset.all(ui)
        remote_dsets = comms.get_user_datasets()

        local_uids = set([dset.generated_uid for dset in local_dsets])
        remote_uids = set([dset["generated_uid"] for dset in remote_dsets])

        # Build data table
        headers = ["UID", "Name", "Data Preparation Cube UID", "Registered", "Local"]

        # Get local dsets information
        local_dsets_data = [
            [
                dset.generated_uid,
                dset.name,
                dset.preparation_cube_uid,
                dset.uid is not None,
                dset.generated_uid in remote_uids,
            ]
            for dset in local_dsets
        ]

        # Get remote dsets information filtered by local
        remote_dsets_data = [
            [dset["generated_uid"], dset["name"], "-", True, False,]
            for dset in remote_dsets
            if dset["generated_uid"] not in local_uids
        ]

        # Combine dsets
        dsets_data = local_dsets_data + remote_dsets_data
        tab = tabulate(dsets_data, headers=headers)
        ui.print(tab)
