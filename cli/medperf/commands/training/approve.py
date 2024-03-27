from medperf import config
from medperf.exceptions import InvalidArgumentError


class TrainingAssociationApproval:
    @staticmethod
    def run(
        training_exp_id: int,
        approval_status,
        data_uid: int = None,
        aggregator: int = None,
    ):
        """Sets approval status for an association between a benchmark and a dataset or mlcube

        Args:
            benchmark_uid (int): Benchmark UID.
            approval_status (str): Desired approval status to set for the association.
            comms (Comms): Instance of Comms interface.
            ui (UI): Instance of UI interface.
            dataset_uid (int, optional): Dataset UID. Defaults to None.
            mlcube_uid (int, optional): MLCube UID. Defaults to None.
        """
        comms = config.comms
        too_many_resources = data_uid and aggregator
        no_resource = data_uid is None and aggregator is None
        if no_resource or too_many_resources:
            raise InvalidArgumentError("Must provide either a dataset or aggregator")

        if data_uid:
            # TODO: show CSR and ask for confirmation
            comms.set_training_dataset_association_approval(
                training_exp_id, data_uid, approval_status.value
            )

        if aggregator:
            comms.set_aggregator_association_approval(
                training_exp_id, aggregator, approval_status.value
            )
