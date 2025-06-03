from medperf.entities.training_exp import TrainingExp
from medperf.entities.event import TrainingEvent
from medperf.utils import approval_prompt, dict_pretty_print, get_participant_label
from medperf.exceptions import CleanExit, InvalidArgumentError
import yaml
import os


class StartEvent:
    @classmethod
    def run(
        cls,
        training_exp_id: int,
        name: str,
        participants_list_file: str = None,
        approval: bool = False,
    ):
        submission = cls(training_exp_id, name, participants_list_file, approval)
        submission.prepare()
        submission.validate()
        submission.prepare_participants_list()
        updated_body = submission.submit()
        submission.write(updated_body)

    def __init__(
        self, training_exp_id: int, name: str, participants_list_file: str, approval
    ):
        self.training_exp_id = training_exp_id
        self.name = name
        self.participants_list_file = participants_list_file
        self.approved = approval

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)

    def validate(self):
        if self.training_exp.approval_status != "APPROVED":
            raise InvalidArgumentError("This experiment has not been approved yet")
        if self.participants_list_file is not None:
            if not os.path.exists(self.participants_list_file):
                raise InvalidArgumentError(
                    "Provided participants list path does not exist"
                )

    def prepare_participants_list(self):
        if self.participants_list_file is None:
            self._prepare_participants_list_from_associations()
        else:
            self._prepare_participants_list_from_file()

    def _prepare_participants_list_from_file(self):
        with open(self.participants_list_file) as f:
            self.participants_list = yaml.safe_load(f)

    def _prepare_participants_list_from_associations(self):
        datasets_with_users = TrainingExp.get_datasets_with_users(self.training_exp_id)
        participants_list = {}
        for dataset in datasets_with_users:
            user_email = dataset["owner"]["email"]
            data_id = dataset["id"]
            participant_label = get_participant_label(user_email, data_id)
            participant_common_name = user_email
            participants_list[participant_label] = participant_common_name
        self.participants_list = participants_list

    def submit(self):
        dict_pretty_print(self.participants_list)
        msg = (
            f"You are about to start an event for the training experiment {self.training_exp.name}."
            " This is the list of participants (participant label, participant common name)"
            " that will be able to participate in your training experiment. Do you confirm? [Y/n] "
        )
        self.approved = self.approved or approval_prompt(msg)

        self.event = TrainingEvent(
            name=self.name,
            training_exp=self.training_exp_id,
            participants=self.participants_list,
        )
        if self.approved:
            updated_body = self.event.upload()
            return updated_body

        raise CleanExit("Event creation cancelled")

    def write(self, updated_body):
        event = TrainingEvent(**updated_body)
        event.write()
