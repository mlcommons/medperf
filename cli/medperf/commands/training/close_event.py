import os
from medperf.entities.training_exp import TrainingExp
from medperf.entities.event import TrainingEvent
from medperf.utils import approval_prompt, dict_pretty_print
from medperf.exceptions import CleanExit, InvalidArgumentError
from medperf import config
import yaml


class CloseEvent:
    """Used for both event cancellation (with custom report path) and for event closing
    (with the expected report path generated by the aggregator)"""

    @classmethod
    def run(cls, training_exp_id: int, report_path: str = None, approval: bool = False):
        submission = cls(training_exp_id, report_path, approval)
        submission.prepare()
        submission.validate()
        submission.read_report()
        submission.submit()
        submission.write()

    def __init__(self, training_exp_id: int, report_path: str, approval: bool):
        self.training_exp_id = training_exp_id
        self.approved = approval
        self.report_path = report_path

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.event = TrainingEvent.from_experiment(self.training_exp_id)
        self.report_path = self.report_path or self.event.get_latest_report_path()

    def validate(self):
        if self.event.finished:
            raise InvalidArgumentError("This experiment has already finished")
        if not os.path.exists(self.report_path):
            raise InvalidArgumentError(f"Report {self.report_path} does not exist.")

    def read_report(self):
        with open(self.report_path) as f:
            self.report = yaml.safe_load(f)

    def submit(self):
        self.event.report = self.report
        body = {"finished": True, "report": self.report}
        dict_pretty_print(self.report)
        msg = (
            f"You are about to close the event of training experiment {self.training_exp.name}."
            " This will be the submitted report. Do you confirm? [Y/n] "
        )
        self.approved = self.approved or approval_prompt(msg)

        if self.approved:
            config.comms.update_training_event(self.event.id, body)
            return
        raise CleanExit("Event closing cancelled")

    def write(self):
        self.event.write()
