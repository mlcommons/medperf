from typing import Dict, Union, Tuple
from medperf.exceptions import InvalidContainerSpec
from medperf.containers.parsers.parser import Parser


class AirflowParser(Parser):
    """
    MedPerf-facing side of the tool to parse YAML files for Airflow.
    The actual DAG generation portion of the parser is implemented separately
    in the `airflow_runner` directory.
    """

    def __init__(self, airflow_config: dict, allowed_runners: list):
        self.airflow_config = airflow_config
        self.allowed_runners = allowed_runners

        # The following variables are set when calling check_schema for the first time
        self._steps = None
        self.pools = None
        self.step_ids = None

    def check_schema(self) -> str:
        """
        This is still the preliminary version of the schema. Subject to change.
        """
        if "steps" not in self.airflow_config:
            raise InvalidContainerSpec("Airflow config should have a 'steps' field.")

        self._steps = self.airflow_config["steps"]
        self.step_ids = []

        final_step_candidates = []
        error_msgs = []
        tmp_pools = {}

        for i, step in enumerate(self._steps):
            self.step_ids.append(step["id"])

            # Check if has minimal fields
            missing_fields_msg = self._check_mandatory_fields(step=step, step_index=i)
            if missing_fields_msg is not None:
                error_msgs.append(missing_fields_msg)
                continue

            # Check last step
            last_step_is_partioned_msg, is_last_step_candidate = self._check_last_step(
                step=step
            )
            if is_last_step_candidate:
                final_step_candidates.append(step["id"])
            if last_step_is_partioned_msg:
                error_msgs.append(last_step_is_partioned_msg)

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

    def _check_mandatory_fields(
        step: Dict[str, str], step_index: int
    ) -> Union[str, None]:
        mandatory_fields = set("id", "type", "command")
        missing_fields = mandatory_fields.difference(set(step.keys()))
        if missing_fields:
            ordered_fields = sorted(list(missing_fields))
            msg = (
                f"The {step_index+1}th step in the yaml file is missing the "
                f"following mandatory fields: ', '.join({ordered_fields})"
            )
            return msg
        else:
            return None

    def _check_last_step(
        step: Dict[str, str], step_index: int
    ) -> Tuple[Union[str, None], bool]:
        is_marked_as_last = step.get("last", False)
        inferred_as_last = step.get("next") is None
        error_msg = None
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
        else:
            is_last_step_candidate = False

        return error_msg, is_last_step_candidate

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
