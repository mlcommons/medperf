from __future__ import annotations
from airflow.sdk import Asset, DAG
from typing import Any
from constants import YESTERDAY
from operator_factory import operator_factory


class DagBuilder:

    def __init__(self, expanded_step: dict[str, Any]):
        raw_inlets = expanded_step.pop("inlets", [])
        self.builder_id = expanded_step["id"]
        self.inlets = [Asset(raw_inlet) for raw_inlet in raw_inlets]
        self.partition = expanded_step.get("partition", None)
        self.operator_builders = operator_factory(**expanded_step)
        self._operator_id_to_builder_obj = {
            operator.operator_id: operator for operator in self.operator_builders
        }
        self._generated_operators = {}

    @property
    def num_operators(self) -> int:
        return len(self.operator_builders)

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.builder_id}, num_ops={self.num_operators})"

    def __repr__(self):
        return str(self)

    @property
    def display_name(self):
        return self.operator_builders[0].display_name

    @property
    def tags(self):
        return self.operator_builders[0].tags

    def build_dag(self):
        schedule = self.inlets or "@once"

        with DAG(
            dag_id=self.builder_id,
            dag_display_name=self.display_name,
            catchup=False,
            max_active_runs=1,
            schedule=schedule,
            start_date=YESTERDAY,
            is_paused_upon_creation=False,
            tags=self.tags,
            auto_register=True,
        ) as dag:
            for operator_builder in self.operator_builders:
                current_operator = self._get_generated_operator_by_id(
                    operator_builder.operator_id
                )

                for next_id in operator_builder.next_ids:
                    next_operator = self._get_generated_operator_by_id(next_id)
                    if next_operator is not None:
                        current_operator >> next_operator
        return dag

    def _get_generated_operator_by_id(
        self,
        operator_id,
    ):
        if operator_id not in self._generated_operators:
            builder_for_this_operator = self._operator_id_to_builder_obj[operator_id]
            self._generated_operators[operator_id] = (
                builder_for_this_operator.get_airflow_operator()
            )
        return self._generated_operators[operator_id]
