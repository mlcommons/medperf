from __future__ import annotations
from airflow.sdk import Asset, BaseOperator
from abc import ABC, abstractmethod
from constants import ALWAYS_CONDITION, FINAL_ASSET


class OperatorBuilder(ABC):
    def __init__(
        self,
        operator_id: str,
        raw_id: str,
        next_ids: list[str] | str = None,
        limit: int = None,
        from_yaml: bool = True,
        make_outlet: bool = True,
        on_error: str = None,
        **kwargs,
    ):
        # TODO add logic to import on_error as a callable
        # Always call this init during subclass inits
        self.operator_id = operator_id
        self.raw_id = raw_id
        self.display_name = self._convert_id_to_display_name(self.raw_id)

        if make_outlet:
            self.next_ids = []
            self.outlets = self._make_outlets(next_ids)
        else:
            self.next_ids = next_ids or []
            self.outlets = None

        self.from_yaml = from_yaml
        if limit is None:
            self.pool_info = None
        else:
            self.pool_info = f'{self.raw_id}_pool'

        self.partition = kwargs.get("partition")
        self.tags = [self.raw_id, self.display_name]
        if self.partition:
            self.tags.append(self.partition)
            self.display_name += f" - {self.partition}"

    def __str__(self):
        return f"{self.__class__.__name__}(operator_id={self.operator_id})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.operator_id)

    def _make_outlets(self, next_ids):
        if next_ids is not None:
            if isinstance(next_ids, str):
                next_ids = [next_ids]
            outlets = [Asset(next_id) for next_id in next_ids]
        else:
            outlets = [Asset(FINAL_ASSET)]
        return outlets

    @staticmethod
    def _convert_id_to_display_name(original_id):
        return original_id.replace("_", " ").title()

    def get_airflow_operator(self) -> BaseOperator:
        base_operator = self._define_base_operator()
        if self.pool_info is not None:
            base_operator.pool = self.pool_info

        if self.outlets:
            base_operator.outlets = self.outlets

        return base_operator

    @abstractmethod
    def _define_base_operator(self) -> BaseOperator:
        """
        Returns the initial definition of the operator object, without defining pools or outlets.
        These, if defined, are patched later in get_airflow_operator.
        """
        pass

    @classmethod
    def build_operator_list(cls, **kwargs) -> list[OperatorBuilder]:
        """
        Helper method to build a list of required Operators for a DAG Builder.
        Usually will return a list with a single element that is the desired operator
        If conditional next_ids are sent from the YAML file, then this will return a list including
        a Python Sensor Operator and a Python Branching Operator, which are both used to deal with branching
        """
        operator_list = []
        kwargs["operator_id"] = kwargs.pop("id", None)

        id_info = kwargs.pop("next", [])
        make_outlet_for_main_operator = True
        if isinstance(id_info, dict):
            # If we have a branching condition in YAML, we return three operators:
            # OperatorFromYAML -> PythonSensorOperator -> PythonBranchOperator -> EmptyOperator -> NextOperatorFromYAML
            # OperatorFromYAML runs as defind by the YAML File.
            # A PythonSensorOperator then waits for any of the defind conditions to be True and
            # forwards the True condition to the PythonBranchOperator, which then branches accordingly.
            # The Sensor and Branch Operators are defined here, so we can adapt the input arguments of the first operator accordingly
            # (ie make it go into sensor that goes into branch which then goes into other operators from the YAML file)
            # Empty operators are used between the branch operator and next operator from YAML to simplify breaking DAG cycles, if any
            # are present. If DAG cycles are not present, the Empty operators do not interfere with DAG execution.
            from .branch_from_sensor_operator_builder import (
                BranchFromSensorOperatorBuilder,
            )
            from .python_sensor_builder import PythonSensorBuilder
            from .empty_operator_builder import EmptyOperatorBuilder

            make_outlet_for_main_operator = False
            conditions_definitions = kwargs.pop(
                "conditions_definitions", []
            )  # [{'id': 'condition_1', 'type': 'function', 'function_name': 'function_name'}...]
            conditions_definitions = {
                condition["id"]: {
                    key: value for key, value in condition.items() if key != "id"
                }
                for condition in conditions_definitions
            }  # {'condition_1: {'type': 'function', 'function_name': 'function_name'}, ...}

            branching_info: list[dict[str, str]] = id_info.pop("if")
            partition = kwargs.get("partition")
            operator_id = kwargs["operator_id"]
            operator_raw_id = kwargs["raw_id"]
            sensor_id = f"conditions_{operator_id}"
            branching_id = f"branch_{operator_id}"
            wait_time = id_info.pop("wait", None)
            default_conditions = id_info.pop("else", [])
            kwargs["next_ids"] = [sensor_id]

            conditions = branching_info
            for default_condition in default_conditions:
                if default_condition and default_condition != kwargs["operator_id"]:
                    conditions.append(
                        {"condition": ALWAYS_CONDITION, "target": default_condition}
                    )
            processed_conditions = []
            for condition in conditions:
                temp_conditions = [
                    {
                        "condition": condition["condition"],
                        "target": f"empty_{operator_id}_{target}",
                    }
                    for target in condition["target"]
                ]
                processed_conditions.extend(temp_conditions)

            empty_ids = [condition["target"] for condition in processed_conditions]
            ids_after_empty = [condition["target"] for condition in conditions]

            sensor_operator = PythonSensorBuilder(
                conditions=processed_conditions,
                raw_id=f"conditions_{operator_raw_id}",
                wait_time=wait_time,
                operator_id=sensor_id,
                next_ids=[branching_id],
                conditions_definitions=conditions_definitions,
                from_yaml=False,
                make_outlet=False,
                partition=partition,
            )

            # TODO this will break!
            empty_operators = [
                EmptyOperatorBuilder(
                    operator_id=empty_id,
                    raw_id=empty_id,
                    from_yaml=False,
                    next_ids=next_id,
                    partition=partition,
                    make_outlet=True,
                )
                for empty_id, next_id in zip(empty_ids, ids_after_empty)
            ]

            branch_operator = BranchFromSensorOperatorBuilder(
                next_ids=[empty_id for empty_id in empty_ids],
                previous_sensor=sensor_operator,
                operator_id=branching_id,
                raw_id=f"branch_{operator_raw_id}",
                from_yaml=False,
                make_outlet=False,
            )
            operator_list.extend([sensor_operator, branch_operator, *empty_operators])
        else:
            kwargs["next_ids"] = id_info

        this_operator = cls(**kwargs, make_outlet=make_outlet_for_main_operator)
        operator_list = [this_operator, *operator_list]
        return operator_list
