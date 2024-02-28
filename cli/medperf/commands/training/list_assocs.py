from tabulate import tabulate

from medperf import config


class ListTrainingAssociations:
    @staticmethod
    def run(filter: str = None):
        """Get training association requests"""
        comms = config.comms
        ui = config.ui
        dset_assocs = comms.get_training_datasets_associations()
        agg_assocs = comms.get_aggregators_associations()

        # Might be worth seeing if creating an association class that encapsulates
        # most of the logic here is useful
        assocs = dset_assocs + agg_assocs
        if filter:
            filter = filter.upper()
            assocs = [assoc for assoc in assocs if assoc["approval_status"] == filter]

        assocs_info = []
        for assoc in assocs:
            assoc_info = (
                assoc.get("dataset", None),
                assoc.get("aggregator", None),
                assoc["training_exp"],
                assoc["initiated_by"],
                assoc["approval_status"],
            )
            assocs_info.append(assoc_info)

        headers = [
            "Dataset UID",
            "Aggregator UID",
            "TrainingExp UID",
            "Initiated by",
            "Status",
        ]
        tab = tabulate(assocs_info, headers=headers)
        ui.print(tab)
