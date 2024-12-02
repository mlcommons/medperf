from tabulate import tabulate

from medperf import config
from medperf.commands.association.utils import validate_args, get_associations_list


class ListAssociations:
    @staticmethod
    def run(
        benchmark,
        training_exp,
        dataset,
        mlcube,
        aggregator,
        ca,
        approval_status,
    ):
        """Get user association requests"""
        validate_args(
            benchmark, training_exp, dataset, mlcube, aggregator, ca, approval_status
        )
        if training_exp:
            experiment_key = "training_exp"
        elif benchmark:
            experiment_key = "benchmark"

        if mlcube:
            component_key = "model_mlcube"
        elif dataset:
            component_key = "dataset"
        elif aggregator:
            component_key = "aggregator"
        elif ca:
            component_key = "ca"

        assocs = get_associations_list(experiment_key, component_key, approval_status)

        assocs_info = []
        for assoc in assocs:
            assoc_info = (
                assoc[component_key],
                assoc[experiment_key],
                assoc["initiated_by"],
                assoc["approval_status"],
            )
            assocs_info.append(assoc_info)

        headers = [
            f"{component_key.replace('_', ' ').title()} UID",
            f"{experiment_key.replace('_', ' ').title()} UID",
            "Initiated by",
            "Status",
        ]
        tab = tabulate(assocs_info, headers=headers)
        config.ui.print(tab)
