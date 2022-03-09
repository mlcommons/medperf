from tabulate import tabulate

from medperf.ui import UI
from medperf.comms import Comms


class Associations:
    @staticmethod
    def run(comms: Comms, ui: UI, filter: str = None):
        """Get Pending association requests"""
        filter = filter.upper()
        dset_assocs = comms.get_dataset_associations()
        cube_assocs = comms.get_cube_associations()

        # Might be worth seeing if creating an association class that encapsulates
        # most of the logic here is useful
        if filter:
            dset_assocs = [
                assoc for assoc in dset_assocs if assoc["approval_status"] == filter
            ]
            cube_assocs = [
                assoc for assoc in cube_assocs if assoc["approval_status"] == filter
            ]

        assocs = dset_assocs + cube_assocs

        assocs_info = []
        for assoc in assocs:
            assoc_info = (
                assoc.get("dataset", "-"),
                assoc.get("model_mlcube", "-"),
                assoc["benchmark"],
                assoc["initiated_by"],
                assoc["approval_status"],
            )
            assocs_info.append(assoc_info)

        headers = [
            "Dataset UID",
            "MLCube UID",
            "Benchmark UID",
            "Initiated by",
            "Status",
        ]
        tab = tabulate(assocs_info, headers=headers)
        ui.print(tab)

