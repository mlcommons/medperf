from .operator_builder import OperatorBuilder
from airflow.sdk import task
from airflow.exceptions import AirflowException


class ManualApprovalBuilder(OperatorBuilder):
    def _define_base_operator(self):

        @task(
            task_id=self.operator_id,
            task_display_name=self.display_name,
            outlets=self.outlets,
        )
        def auto_fail():
            raise AirflowException("This task must be approved manually!")

        task_instance = auto_fail()
        return task_instance

    @classmethod
    def build_operator_list(cls, **kwargs):
        """
        An Empty Operator must be added after this operator so that the downstream
        Asset triggers properly after manually setting this task as Success.
        If necessary, it is added here.
        """
        from .empty_operator_builder import EmptyOperatorBuilder

        initial_operator_list = super().build_operator_list(**kwargs)
        if len(initial_operator_list) > 1:
            return initial_operator_list

        original_approval_operator = initial_operator_list[0]

        empty_id = f"empty_{original_approval_operator.operator_id}"
        empty_operator_builder = EmptyOperatorBuilder(
            operator_id=empty_id,
            raw_id=f"empty_{original_approval_operator.raw_id}",
            next_ids=kwargs.get("next_ids", kwargs.get("next", [])),
            make_outlet=True,
            from_yaml=False,
        )
        new_approval_operator = ManualApprovalBuilder(
            operator_id=original_approval_operator.operator_id,
            raw_id=original_approval_operator.raw_id,
            next_ids=[empty_id],
            make_outlet=False,
        )

        return [new_approval_operator, empty_operator_builder]
