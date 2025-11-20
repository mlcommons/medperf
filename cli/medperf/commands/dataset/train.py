import os
from medperf import config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.entities.ca import CA
from medperf.entities.event import TrainingEvent
from medperf.exceptions import (
    CleanExit,
    ExecutionError,
    InvalidArgumentError,
    MedperfException,
)
from medperf.entities.training_exp import TrainingExp
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.utils import (
    approval_prompt,
    dict_pretty_print,
    get_pki_assets_path,
    get_participant_label,
    remove_path,
)
from medperf.certificates import verify_certificate_authority


class TrainingExecution:
    @classmethod
    def run(
        cls,
        training_exp_id: int,
        data_uid: int,
        overwrite: bool = False,
        approved: bool = False,
        restart_on_failure: bool = False,
        skip_restart_on_failure_prompt: bool = False,
    ):
        """Starts the aggregation server of a training experiment

        Args:
            training_exp_id (int): Training experiment UID.
        """
        if restart_on_failure:
            approved = True
            overwrite = True
        execution = cls(training_exp_id, data_uid, overwrite, approved)
        if restart_on_failure and not skip_restart_on_failure_prompt:
            execution.confirm_restart_on_failure()

        while True:
            execution.prepare()
            execution.validate()
            execution.check_existing_outputs()
            execution.prepare_plan()
            execution.prepare_pki_assets()
            execution.confirm_run()
            with config.ui.interactive():
                execution.prepare_training_cube()
                try:
                    execution.run_experiment()
                    break
                except ExecutionError as e:
                    print(str(e))
                    if not restart_on_failure:
                        break

    def __init__(
        self, training_exp_id: int, data_uid: int, overwrite: bool, approved: bool
    ) -> None:
        self.training_exp_id = training_exp_id
        self.data_uid = data_uid
        self.overwrite = overwrite
        self.ui = config.ui
        self.approved = approved

    def confirm_restart_on_failure(self):
        msg = (
            "You chose to restart on failure. This means that the training process"
            " will automatically restart, without your approval, even if training configuration"
            " changes from the server side. Do you confirm? [Y/n] "
        )
        if not approval_prompt(msg):
            raise CleanExit(
                "Training cancelled. Rerun without the --restart_on_failure flag."
            )

    def prepare(self):
        self.training_exp = TrainingExp.get(self.training_exp_id)
        self.ui.print(f"Training Execution: {self.training_exp.name}")
        self.event = TrainingEvent.from_experiment(self.training_exp_id)
        self.dataset = Dataset.get(self.data_uid)
        self.user_email: str = get_medperf_user_data()["email"]
        self.out_logs = os.path.join(self.event.col_out_logs, str(self.dataset.id))

    def validate(self):
        if self.dataset.id is None:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        if self.dataset.state != "OPERATION":
            msg = "The provided dataset is not operational."
            raise InvalidArgumentError(msg)

        if self.event.finished:
            msg = "The provided training experiment has to start a training event."
            raise InvalidArgumentError(msg)

    def check_existing_outputs(self):
        msg = (
            "Outputs still exist from previous runs. Overwrite"
            " them by rerunning the command with --overwrite"
        )
        paths = [self.out_logs]
        for path in paths:
            if os.path.exists(path):
                if not self.overwrite:
                    raise MedperfException(msg)
                remove_path(path)

    def prepare_plan(self):
        self.training_exp.prepare_plan()

    def prepare_pki_assets(self):
        ca = CA.get(config.certificate_authority_id)
        verify_certificate_authority(
            ca, expected_fingerprint=config.certificate_authority_fingerprint
        )
        self.dataset_pki_assets = get_pki_assets_path(self.user_email, ca.id)
        self.ca = ca

    def confirm_run(self):
        msg = (
            "Above is the training configuration that will be used."
            " Do you confirm starting training? [Y/n] "
        )
        dict_pretty_print(self.training_exp.plan)
        self.approved = self.approved or approval_prompt(msg)

        if not self.approved:
            raise CleanExit("Training cancelled.")

    def prepare_training_cube(self):
        self.cube = self.__get_cube(self.training_exp.fl_mlcube, "FL")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = (
            "Retrieving and setting up training container. This may take some time."
        )
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> Container '{name}' download complete")
        return cube

    def run_experiment(self):
        participant_label = get_participant_label(self.user_email, self.dataset.id)
        env = {"MEDPERF_PARTICIPANT_LABEL": participant_label}
        mounts = {
            "data_path": self.dataset.data_path,
            "labels_path": self.dataset.labels_path,
            "node_cert_folder": self.dataset_pki_assets,
            "ca_cert_folder": self.ca.pki_assets,
            "plan_path": self.training_exp.plan_path,
            "output_logs": self.out_logs,
        }

        self.ui.text = "Running Training"
        self.cube.run(task="train", mounts=mounts, env=env, disable_network=False)
