import yaml
import os
from constants import YAML_DIR
from typing import Union, Any
from dag_utils import import_external_python_function
from collections import defaultdict
from airflow.sdk import DAG
from dag_utils import create_legal_dag_id
from dag_builder import DagBuilder
from copy import deepcopy


class YamlParser:

    def __init__(self, yaml_dir_path: str = None):
        self.yaml_dir_path = yaml_dir_path or YAML_DIR
        yaml_content = self.read_yaml_definition()
        self.raw_steps = yaml_content["steps"]
        self._raw_conditions = yaml_content.get("conditions", [])
        self._raw_subject_definitions = yaml_content.get("per_subject_def", {})
        self.dag_builders = None

    @staticmethod
    def read_yaml_definition() -> (
        dict[str, Union[list[dict[str, str]], dict[str, str]]]
    ):
        yaml_files = [yaml_file for yaml_file in os.listdir(YAML_DIR)]
        yaml_files = [os.path.join(YAML_DIR, yaml_file) for yaml_file in yaml_files]
        yaml_files = [
            yaml_file
            for yaml_file in yaml_files
            if os.path.isfile(yaml_file)
            and (yaml_file.endswith(".yaml") or yaml_file.endswith(".yml"))
        ]

        if len(yaml_files) == 0:
            raise ValueError("No YAML files found!")
        elif len(yaml_files) > 1:
            raise ValueError(
                "More than one YAML file found! The parser currently only supports parsing a single file!"
            )

        yaml_file = yaml_files[0]
        try:
            with open(yaml_file, "r") as f:
                raw_content = f.read()
                expanded_content = os.path.expandvars(raw_content)
                yaml_info = yaml.safe_load(expanded_content)
        except Exception:
            print(f"Unable to load YAML file {yaml_file}. It will be skipped.")

        return yaml_info

    def read_subject_partitions(self):
        from pipeline_state import PipelineState

        if not self._raw_subject_definitions:
            return []

        per_subjection_function_name = self._raw_subject_definitions["function_name"]
        per_subject_function_obj = import_external_python_function(
            per_subjection_function_name
        )
        subject_partition_list = per_subject_function_obj(PipelineState())
        return subject_partition_list

    def _get_next_id_from_expanded_step(self, raw_step):
        next_field = raw_step.get("next")
        if next_field is None:
            return []
        elif isinstance(next_field, str):
            return [next_field]
        elif isinstance(next_field, list):
            return next_field
        else:
            if_fields = next_field.get("if", [])
            default_fields = next_field.get("else", None)
            next_fields = [
                target for if_field in if_fields for target in if_field["target"]
            ]
            if default_fields:
                next_fields.extend(default_fields)
            return next_fields

    def _update_next_id_in_expanded_step(
        self, current_step, id_to_partition_to_partition_id
    ):
        next_field = deepcopy(current_step.get("next"))
        this_partition = current_step["partition"]

        def get_updated_ids(this_partition, partition_to_partition_id):
            if this_partition is None:
                # This step is not partitioned, but leads to a partition -> use all as next
                updated_ids = list(partition_to_partition_id.values())
            else:
                # This step is also partitioned. Pick corresponding partition
                updated_ids = [partition_to_partition_id[this_partition]]
            return updated_ids

        def update_next_ids(original_next_ids):
            new_ids = []
            for next_id in original_next_ids:
                partition_to_partition_id = id_to_partition_to_partition_id.get(next_id)
                if not partition_to_partition_id:
                    new_ids.append(next_id)
                    continue

                updated_ids = get_updated_ids(
                    this_partition=this_partition,
                    partition_to_partition_id=partition_to_partition_id,
                )
                new_ids.extend(updated_ids)
            return new_ids

        if not next_field:
            return
        elif isinstance(next_field, str):
            next_field = [next_field]

        if isinstance(next_field, list):
            updated_next = update_next_ids(next_field)
            next_field = updated_next
        else:
            if_fields = next_field.get("if", [])
            for if_field in if_fields:
                next_ids = if_field["target"]

                if isinstance(next_ids, str):
                    next_ids = [next_ids]
                updated_ids = update_next_ids(next_ids)
                if_field["target"] = updated_ids

            default_field = next_field.get("else")
            if default_field:
                if isinstance(default_field, str):
                    default_field = [default_field]
                new_default = update_next_ids(default_field)
                next_field["else"] = new_default

        return next_field

    def _verify_unique_id(self, potential_id, original_id, mapped_steps):
        if potential_id in mapped_steps:
            raise ValueError(f"ID {original_id} has been used more than one time!")

    def _create_expanded_steps(
        self, raw_steps: list[dict[str, Any]], subject_partitions: list[str]
    ):
        step_id_to_expanded_step = {}
        original_id_to_partition_to_partitioned_id = defaultdict(dict)
        for step in raw_steps:
            original_id = step["id"]
            step["conditions_definitions"] = self._raw_conditions
            if step.get("per_subject"):
                for subject_partition in subject_partitions:
                    partitioned_step = {k: v for k, v in step.items()}
                    partitioned_id = create_legal_dag_id(
                        f"{original_id}_{subject_partition}"
                    )
                    self._verify_unique_id(
                        potential_id=partitioned_id,
                        original_id=original_id,
                        mapped_steps=step_id_to_expanded_step,
                    )

                    partitioned_step["id"] = partitioned_id
                    partitioned_step["raw_id"] = original_id
                    partitioned_step["partition"] = subject_partition
                    step_id_to_expanded_step[partitioned_step["id"]] = partitioned_step
                    original_id_to_partition_to_partitioned_id[original_id][
                        subject_partition
                    ] = partitioned_id
            else:
                step["partition"] = None
                step_id = create_legal_dag_id(original_id)
                step["id"] = step_id
                step["raw_id"] = original_id
                self._verify_unique_id(
                    potential_id=step_id,
                    original_id=original_id,
                    mapped_steps=step_id_to_expanded_step,
                )
                step_id_to_expanded_step[step_id] = step

        for step_id, step in step_id_to_expanded_step.items():
            new_next = self._update_next_id_in_expanded_step(
                step, original_id_to_partition_to_partitioned_id
            )
            step["next"] = new_next

        next_id_to_upstream_ids = defaultdict(set)
        for step_id, step in step_id_to_expanded_step.items():
            next_ids = self._get_next_id_from_expanded_step(step)
            for next_id in next_ids:
                next_id_to_upstream_ids[next_id].add(step_id)

        for step_id, step in step_id_to_expanded_step.items():
            upstream_ids = list(next_id_to_upstream_ids[step_id])
            if upstream_ids:
                this_step_inlets = []
                if step["partition"] is None:
                    for upstream_id in upstream_ids:
                        upstream_dict = step_id_to_expanded_step[upstream_id]
                        upstream_partition = upstream_dict["partition"]
                        if upstream_partition:
                            new_inlet = create_legal_dag_id(
                                f"{step_id}_{upstream_partition}"
                            )
                            this_step_inlets.append(new_inlet)
                            self._update_next_with_new_partition(
                                upstream_dict, step_id, new_inlet
                            )
                if not this_step_inlets:
                    this_step_inlets = [step_id]
                step["inlets"] = this_step_inlets
            else:
                step["inlets"] = []

        expanded_steps = list(step_id_to_expanded_step.values())
        return expanded_steps

    def _update_next_with_new_partition(self, original_dict, original_next, new_next):
        next_field = original_dict["next"]
        if isinstance(next_field, list):
            next_field = [
                item if item != original_next else new_next for item in next_field
            ]
        else:
            if_fields = next_field["if"]
            if_fields = [
                item if item != original_next else new_next for item in if_fields
            ]
            default_fields = next_field["else"]
            default_fields = [
                item if item != original_next else new_next for item in default_fields
            ]
        original_dict["next"] = next_field

    def map_dag_builders_from_yaml(self) -> list[DagBuilder]:

        subject_partitions = self.read_subject_partitions()
        expanded_steps = self._create_expanded_steps(
            self.raw_steps, subject_partitions=subject_partitions
        )
        dag_builder_list = [
            DagBuilder(expanded_step=expanded_step) for expanded_step in expanded_steps
        ]

        return dag_builder_list

    def build_dags(self) -> list[DAG]:
        if self.dag_builders is None:
            self.dag_builders = self.map_dag_builders_from_yaml()

        dags_list = [builder.build_dag() for builder in self.dag_builders]
        return dags_list
