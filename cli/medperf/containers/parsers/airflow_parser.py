from typing import Dict, Union
from medperf.exceptions import InvalidContainerSpec
from medperf.containers.parsers.parser import Parser


class AirflowParser(Parser):
    """
    MedPerf-facing side of the tool to parse YAML files for Airflow.
    The actual DAG generation portion of the parser is implemented separately
    in the `airflow_runner` directory.
    """

    def __init__(
        self, airflow_config: dict, allowed_runners: list, config_file_path: str
    ):
        self.airflow_config = airflow_config
        self.allowed_runners = allowed_runners
        self.config_file_path = config_file_path

        # The following variables are set when calling check_schema for the first time
        self._steps = []
        self.pools = None
        self.step_ids = []
        self.container_ids = (
            []
        )  # TODO currently assumes only images on some registry, does not support files

    def check_schema(self) -> str:
        """
        This is still the preliminary version of the schema. Subject to change.
        """
        if "steps" not in self.airflow_config:
            raise InvalidContainerSpec("Airflow config should have a 'steps' field.")

        self._steps = self.airflow_config["steps"]

        final_step_candidates = []
        error_msgs = []
        tmp_pools = {}

        for i, step in enumerate(self._steps):
            self.step_ids.append(step["id"])

            self._check_mandatory_fields(
                step=step, step_index=i, error_msg_list=error_msgs
            )

            is_last_step_candidate = self._check_last_step(
                step=step, error_msg_list=error_msgs
            )
            if is_last_step_candidate:
                final_step_candidates.append(step["id"])

            container_image = self._verify_container(step, error_msg_list=error_msgs)
            if container_image is not None:
                self.container_ids.append(container_image)

            if "limit" in step.keys():
                tmp_pools.update(self._create_pool_info(step))

        if not final_step_candidates:
            msg = "The provided YAML DAG file has no clear final step!"
            error_msgs.append(msg)

        elif len(final_step_candidates) > 1:
            msg = "The provided YAML DAG file has multiple potential last steps. Please verify the following steps:\n"
            msg += "\n".join(final_step_candidates)
            error_msgs.append(msg)

        if error_msgs:
            full_msg = "\n\n".join(error_msgs)
            raise InvalidContainerSpec(full_msg)

        self.pools = tmp_pools or None

    @staticmethod
    def _check_mandatory_fields(
        step: Dict[str, str], step_index: int, error_msg_list: list[str]
    ) -> Union[str, None]:
        mandatory_fields = {"id", "type"}
        missing_fields = mandatory_fields.difference(set(step.keys()))
        if missing_fields:
            ordered_fields = sorted(list(missing_fields))
            if step.get("id"):
                step_identifier = f"step {step['id']}"
            else:
                step_identifier = f"{step_index+1}th step"
            msg = (
                f"The {step_identifier} in the yaml file is missing the "
                f"following mandatory fields: ', '.join({ordered_fields})"
            )
            error_msg_list.append(msg)

    @staticmethod
    def _check_last_step(step: Dict[str, str], error_msg_list: list[str]) -> bool:
        is_marked_as_last = step.get("last", False)
        inferred_as_last = step.get("next") is None

        if is_marked_as_last or inferred_as_last:
            is_last_step_candidate = True
            if step.get("per_subject", False):
                error_msg = f"Step {step['id']} appears to be the final step, but is also part of a partition.\n"
                error_msg += (
                    "Please make sure the final step is not part of any partitions. "
                )
                error_msg += (
                    "You may need to add a final dummy step to join all results."
                )
                error_msg_list.append(error_msg)
        else:
            is_last_step_candidate = False

        return is_last_step_candidate

    @staticmethod
    def _create_pool_info(step: Dict[str, Union[str, int]]):
        return {
            f'{step["id"]}_pool': {
                "slots": step["limit"],
                "include_deferred": False,
                "description": f"Pool to limit the execution of "
                f'tasks with ID {step["id"]} to {step["limit"]} '
                "parallel executions",
            }
        }

    @staticmethod
    def _verify_container(step: Dict[str, str], error_msg_list: list[str]):
        if step.get("type") != "container":
            return None

        if "command" not in step:
            msg = f"Step {step['id']} is of type 'container' bu does not specify a 'command' field!"
            error_msg_list.append(msg)

        try:
            return step["image"]
        except KeyError:
            msg = f"Step {step['id']} is of type 'container' but does not specify a 'image' field!!"
            error_msg_list.append(msg)
            return None

    # TODO validate how to add these methods to this parser
    def check_task_schema(self, task):
        pass

    def get_setup_args(self):
        pass

    def get_volumes(self, task: str, medperf_mounts: dict):
        pass

    def get_run_args(self, task: str, medperf_mounts: dict):
        pass

    def is_report_specified(self):
        pass

    def is_metadata_specified(self):
        pass
