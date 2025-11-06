from .operator_builder import OperatorBuilder
from airflow.providers.standard.operators.empty import EmptyOperator


class EmptyOperatorBuilder(OperatorBuilder):

    def _define_base_operator(self):

        return EmptyOperator(
            task_id=self.operator_id,
            task_display_name=self.display_name,
            outlets=self.outlets,
        )
