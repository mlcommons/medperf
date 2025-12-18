from medperf.containers.runners.airflow_runner_utils.dags.operator_builders.operator_builder import (
    OperatorBuilder,
)
from airflow.providers.standard.operators.hitl import ApprovalOperator


class ManualApprovalBuilder(OperatorBuilder):
    def _define_base_operator(self):

        return ApprovalOperator(
            task_id=self.operator_id,
            subject="Manual Approval Task",
            fail_on_reject=True,
            body="Please confirm all generated results before approving the workflow.",
        )
