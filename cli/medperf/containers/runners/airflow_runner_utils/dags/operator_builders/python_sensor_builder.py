from __future__ import annotations
from .operator_builder import OperatorBuilder
from airflow.decorators import task
from airflow.sensors.base import PokeReturnValue
from copy import deepcopy
from pipeline_state import PipelineState
from constants import ALWAYS_CONDITION
from datetime import timedelta
from dag_utils import import_external_python_function

DEFAULT_WAIT_TIME = timedelta(seconds=60)


class Condition:

    def __init__(
        self,
        condition_id: str,
        next_id: str,
        conditions_definitions: dict[str, dict[str, str]],
    ):
        self.condition_id = condition_id
        self.next_id = next_id

        if self.condition_id == ALWAYS_CONDITION:
            self.type = ALWAYS_CONDITION
            self.complete_function_name = None

        else:
            this_definition = conditions_definitions[self.condition_id]
            self.type = this_definition["type"]  # Currently unused
            self.complete_function_name = this_definition["function_name"]


def evaluate_external_condition(condition: Condition, pipeline_state: PipelineState):
    # TODO implement properly! Should call the external python files and define a
    # pipeline object from airflow_kwargs that is sent to the Python callable.
    # For this first proof of concept, hardcode functions just to validate functionality.
    if condition.condition_id == ALWAYS_CONDITION:
        return True

    condition_function_obj = import_external_python_function(
        condition.complete_function_name
    )
    print(f"Checking condition {condition.condition_id}...")
    condition_result = condition_function_obj(pipeline_state)

    if condition_result:
        print(f"Condition {condition.condition_id} met!")
    else:
        print(f"Condition {condition.condition_id} not met.")
    return condition_result


class PythonSensorBuilder(OperatorBuilder):

    def __init__(
        self,
        conditions: list[dict[str, str]],
        conditions_definitions: dict[str, dict[str, str]],
        wait_time: float = 60,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.conditions = [
            Condition(
                condition_id=condition["condition"],
                next_id=condition["target"],
                conditions_definitions=conditions_definitions,
            )
            for condition in conditions
        ]
        self.wait_time = wait_time or DEFAULT_WAIT_TIME

    def _define_base_operator(self):

        @task.sensor(
            poke_interval=self.wait_time,
            mode="reschedule",
            task_id=self.operator_id,
            task_display_name=self.display_name,
            outlets=self.outlets,
        )
        def wait_for_conditions(**kwargs):
            pipeline_state = PipelineState(running_subject=self.partition, **kwargs)

            for condition in self.conditions:
                if evaluate_external_condition(condition, pipeline_state):
                    return PokeReturnValue(is_done=True, xcom_value=condition.next_id)

            return False

        return wait_for_conditions()
