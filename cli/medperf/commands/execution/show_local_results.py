from medperf.entities.execution import Execution
import yaml
import json
from typing import Union

from medperf import config

from medperf.exceptions import InvalidArgumentError


class ShowLocalResults:
    @staticmethod
    def run(execution_id: Union[int, str], format: str = "yaml", output: str = None):
        show_local_results = ShowLocalResults(execution_id, format, output)
        show_local_results.validate()
        show_local_results.prepare()
        if output is None:
            show_local_results.display()
        else:
            show_local_results.store()

    def __init__(
        self, execution_id: Union[int, str], format: str = "yaml", output: str = None
    ):
        self.execution_id = execution_id
        self.format = format
        self.output = output
        self.results = {}

    def validate(self):
        valid_formats = set(["yaml", "json"])
        if self.format not in valid_formats:
            raise InvalidArgumentError("The provided format is not supported")

    def prepare(self):
        execution = Execution.get(self.execution_id)
        if not execution.is_executed():
            raise InvalidArgumentError("The provided execution has no results yet.")

        self.results = execution.read_results()

    def display(self):
        if self.format == "json":
            formatter = json.dumps
        if self.format == "yaml":
            formatter = yaml.dump

        formatted_data = formatter(self.results)
        config.ui.print(formatted_data)

    def store(self):
        if self.format == "json":
            formatter = json.dump
        if self.format == "yaml":
            formatter = yaml.dump

        with open(self.output, "w") as f:
            formatter(self.results, f)
