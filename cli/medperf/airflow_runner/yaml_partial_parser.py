import yaml
import os
from typing import Dict, Union


class YamlPartialParser:
    """
    Does the initial partial parsing of the DAG YAML directory.
    THe directory should contain a single YAML file and optionally python files to support its execution.
    This parsing simply finds which steps require pools and the final step in the DAG.
    Complete parsing for DAG generation is delegated to the Parser in the DAGs directory.
    """

    YAML_EXTENSIONS = (".yaml", ".yml")

    def __init__(self, yaml_file_dir: os.PathLike):
        self.yaml_dir_path = yaml_file_dir
        self.yaml_path = None
        self.pools = {}
        self.step_ids = []
        self._parse_yaml_dir()

    def _parse_yaml_dir(self):
        file_candidates = [
            filename
            for filename in os.listdir(self.yaml_dir_path)
            if filename.endswith(self.YAML_EXTENSIONS)
        ]

        if not file_candidates:
            raise ValueError(
                f"No YAML file was found in the directory {self.yaml_dir_path}"
            )

        elif len(file_candidates) > 1:
            raise ValueError(
                f"Multiple YAML files found at directory {self.yaml_dir_path}. Please make sure only one file is supplied!"
            )

        self.yaml_path = os.path.join(self.yaml_dir_path, file_candidates[0])
        self._parse_yaml_file()

    def _parse_yaml_file(self):
        final_step_candidates = []
        error_msgs = []
        tmp_pools = {}

        with open(self.yaml_path, "r") as f:
            yaml_content = yaml.safe_load(f)

        for step in yaml_content["steps"]:
            self.step_ids.append(step["id"])
            is_marked_as_last = step.get("last", False)
            inferred_as_last = step.get("next") is None
            if is_marked_as_last or inferred_as_last:
                if step.get("per_subject", False):
                    msg = f"Step {step['id']} appears to be the final step, but is also part of a partition.\n"
                    msg += "Please make sure the final step is not part of any partitions. "
                    msg += "You may need to add a final dummy step to join all results."
                    error_msgs.append(msg)
                else:
                    final_step_candidates.append(step["id"])

            if "limit" in step.keys() and "id" in step.keys():
                tmp_pools.update(self._create_pool_info(step))

        if not final_step_candidates:
            msg = "The provided YAML DAG file has no clear final step!"
            error_msgs.append(msg)

        elif len(final_step_candidates) > 1:
            msg = "The provided YAML DAG has multiple potential last steps. Please verify the following steps:\n"
            msg += "\n".join(final_step_candidates)
            error_msgs.append(msg)

        if error_msgs:
            full_msg = "\n\n".join(error_msgs)
            raise ValueError(full_msg)

        self.pools = tmp_pools or None

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
