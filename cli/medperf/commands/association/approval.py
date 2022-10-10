from medperf import config
from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.utils import pretty_error


class Approval:
    @staticmethod
    def run(
        benchmark_uid: str,
        approval_status: str,
        dataset_uid: str = None,
        mlcube_uid: str = None,
        comms: Comms = config.comms,
        ui: UI = config.ui
    ):
        """Sets approval status for an association between a benchmark and a dataset or mlcube

        Args:
            benchmark_uid (str): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            dataset_uid (str, optional): Dataset UID. Defaults to None.
            mlcube_uid (str, optional): MLCube UID. Defaults to None.
            comms (Comms, optional): Communications instance. Defaults to config.comms
            ui (UI, optional): UI instance. Defaults to config.ui
        """
        too_many_resources = dataset_uid and mlcube_uid
        no_resource = dataset_uid is None and mlcube_uid is None
        if no_resource or too_many_resources:
            pretty_error(
                "Invalid arguments. Must provide either a dataset or mlcube", ui
            )

        if dataset_uid:
            comms.set_dataset_association_approval(
                benchmark_uid, dataset_uid, approval_status.value
            )

        if mlcube_uid:
            comms.set_mlcube_association_approval(
                benchmark_uid, mlcube_uid, approval_status.value
            )
