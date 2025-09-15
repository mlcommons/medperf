from medperf.account_management.account_management import get_medperf_user_data
from medperf.entities.training_exp import TrainingExp
from medperf.entities.cube import Cube
from medperf.exceptions import InvalidArgumentError


class SubmitJob:
    @classmethod
    def run(cls, training_exp_id: int):
        submission = cls(training_exp_id)
        submission.prepare()
        submission.validate()
        submission.start_federation()

    def __init__(self, training_exp_id: int):
        self.training_exp_id = training_exp_id

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.training_exp.prepare_plan()

    def validate(self):
        if self.training_exp.approval_status != "APPROVED":
            raise InvalidArgumentError("This experiment has not been approved yet")

    def start_federation(self):
        participant_label = get_medperf_user_data()["email"]
        env = {"MEDPERF_PARTICIPANT_LABEL": participant_label}
        admin_mlcube_id = self.training_exp.fl_admin_mlcube
        admin_mlcube = Cube.get(admin_mlcube_id)
        if not admin_mlcube.has_task("start_federation"):
            return

        fl_workspace = self.training_exp.get_admin_kit_path()
        plan = self.training_exp.plan_path
        mounts = {"fl_workspace": fl_workspace, "plan_path": plan}

        admin_mlcube.run(
            task="start_federation",
            mounts=mounts,
            env=env,
            disable_network=False,
        )
