from tabulate import tabulate

from medperf import config
from medperf.commands.association.utils import validate_args, get_user_associations


class ListAssociations:
    @staticmethod
    def run(
        approval_status,
        benchmark=False,
        training_exp=False,
        dataset=False,
        mlcube=False,
        aggregator=False,
        ca=False,
    ):
        """Get user association requests"""
        validate_args(
            benchmark, training_exp, dataset, mlcube, aggregator, ca, approval_status
        )
        if training_exp:
            experiment_type = "training_exp"
        elif benchmark:
            experiment_type = "benchmark"

        if mlcube:
            component_type = "model_mlcube"
        elif dataset:
            component_type = "dataset"
        elif aggregator:
            component_type = "aggregator"
        elif ca:
            component_type = "ca"

        assocs = get_user_associations(experiment_type, component_type, approval_status)

        assocs_info = []
        for assoc in assocs:
            assoc_info = (
                assoc[component_type],
                assoc[experiment_type],
                assoc["initiated_by"],
                assoc["approval_status"],
            )
            assocs_info.append(assoc_info)

        headers = [
            f"{component_type.replace('_mlcube', '').replace('_', ' ').title()} UID",
            f"{experiment_type.replace('_', ' ').title()} UID",
            "Initiated by",
            "Status",
        ]
        tab = tabulate(assocs_info, headers=headers)
        config.ui.print(tab)
