from tabulate import tabulate

from medperf import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms


class ListAssociations:
    @staticmethod
    def run(filter: str = None, comms: Comms = config.comms, ui: UI = config.ui):
        """Get Pending association requests

        Args:
            filter (str, optional): String to filter associations by approval status
            comms (Comms, optional): Communications instance. Defaults to config.comms
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        dset_assocs = comms.get_datasets_associations()
        cube_assocs = comms.get_cubes_associations()

        # Might be worth seeing if creating an association class that encapsulates
        # most of the logic here is useful
        assocs = dset_assocs + cube_assocs
        if filter:
            filter = filter.upper()
            assocs = [assoc for assoc in assocs if assoc["approval_status"] == filter]

        assocs_info = []
        for assoc in assocs:
            assoc_info = (
                assoc.get("dataset", None),
                assoc.get("model_mlcube", None),
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
