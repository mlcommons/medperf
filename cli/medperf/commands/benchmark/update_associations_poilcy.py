import os

import medperf.config as config
from medperf.enums import AutoApprovalMode
from medperf.exceptions import InvalidArgumentError
from medperf.utils import sanitize_path
from email_validator import validate_email, EmailNotValidError


class UpdateAssociationsPolicy:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        dataset_auto_approve_mode: str = None,
        dataset_auto_approve_file: str = None,
        model_auto_approve_mode: str = None,
        model_auto_approve_file: str = None,
    ):
        update_policy = cls(
            benchmark_uid,
            dataset_auto_approve_mode,
            dataset_auto_approve_file,
            model_auto_approve_mode,
            model_auto_approve_file,
        )
        update_policy.validate()
        update_policy.read_and_files_contents()
        update_policy.update()

    def __init__(
        self,
        benchmark_uid: int,
        dataset_auto_approve_mode: str = None,
        dataset_auto_approve_file: str = None,
        model_auto_approve_mode: str = None,
        model_auto_approve_file: str = None,
    ):
        self.benchmark_uid = benchmark_uid
        self.dataset_auto_approve_mode = dataset_auto_approve_mode
        self.dataset_auto_approve_file = sanitize_path(dataset_auto_approve_file)
        self.model_auto_approve_mode = model_auto_approve_mode
        self.model_auto_approve_file = sanitize_path(model_auto_approve_file)
        self.allowed_dataset_emails = None
        self.allowed_model_emails = None

    def __validate_mode(self, mode):
        if mode is None:
            return
        modes = [e.value for e in AutoApprovalMode]
        mode = mode.upper()
        if mode not in modes:
            raise InvalidArgumentError(
                f"auto_approve_mode should be one of {modes}. Got {mode}"
            )
        return mode

    def __validate_file_existance(self, file):
        if file is None:
            return
        if not os.path.exists(file):
            raise InvalidArgumentError(f"File {file} does not exist")

    def validate(self):
        self.dataset_auto_approve_mode = self.__validate_mode(
            self.dataset_auto_approve_mode
        )
        self.model_auto_approve_mode = self.__validate_mode(
            self.model_auto_approve_mode
        )
        self.__validate_file_existance(self.dataset_auto_approve_file)
        self.__validate_file_existance(self.model_auto_approve_file)

    def __read_and_validate_file_contents(self, file):
        if file is None:
            return
        with open(file) as f:
            contents = f.read()
        allowed_emails = contents.strip().split("\n")
        allowed_emails = [
            email.lower().strip() for email in allowed_emails if email.strip()
        ]
        for email in allowed_emails:
            try:
                validate_email(email, check_deliverability=False)
            except EmailNotValidError as e:
                raise InvalidArgumentError(str(e))
        return allowed_emails

    def read_and_files_contents(self):
        self.allowed_dataset_emails = self.__read_and_validate_file_contents(
            self.dataset_auto_approve_file
        )

        self.allowed_model_emails = self.__read_and_validate_file_contents(
            self.model_auto_approve_file
        )

    def update(self):
        if all(
            [
                self.allowed_dataset_emails is None
                and self.allowed_model_emails is None
                and self.dataset_auto_approve_mode is None
                and self.model_auto_approve_mode is None
            ]
        ):
            return
        body = {}
        if self.allowed_dataset_emails is not None:
            body["dataset_auto_approval_allow_list"] = self.allowed_dataset_emails
        if self.allowed_model_emails is not None:
            body["model_auto_approval_allow_list"] = self.allowed_model_emails
        if self.dataset_auto_approve_mode is not None:
            body["dataset_auto_approval_mode"] = self.dataset_auto_approve_mode
        if self.model_auto_approve_mode is not None:
            body["model_auto_approval_mode"] = self.model_auto_approve_mode

        config.comms.update_benchmark(self.benchmark_uid, body)
