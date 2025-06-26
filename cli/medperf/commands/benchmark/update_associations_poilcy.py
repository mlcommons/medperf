import os

import medperf.config as config
from medperf.entities.benchmark import Benchmark
from medperf.enums import AutoApprovalMode
from medperf.exceptions import InvalidArgumentError
from medperf.utils import sanitize_path
from email_validator import validate_email, EmailNotValidError


class UpdateAssociationsPolicy:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        auto_approve_mode: str = None,
        auto_approve_file: str = None,
    ):
        update_policy = cls(benchmark_uid, auto_approve_mode, auto_approve_file)
        update_policy.validate()
        update_policy.prepare()
        update_policy.read_and_validate_auto_approve_file()
        update_policy.update()

    def __init__(
        self,
        benchmark_uid: int,
        auto_approve_mode: str = None,
        auto_approve_file: str = None,
    ):
        self.benchmark_uid = benchmark_uid
        self.auto_approve_mode = auto_approve_mode
        self.auto_approve_file = sanitize_path(auto_approve_file)
        self.benchmark = None
        self.allowed_emails = None

    def validate(self):
        modes = [e.value for e in AutoApprovalMode]
        self.auto_approve_mode = self.auto_approve_mode.upper()
        if self.auto_approve_mode.upper() not in modes:
            raise InvalidArgumentError(
                f"auto_approve_mode should be one of {modes}. Got {self.auto_approve_mode}"
            )

        if self.auto_approve_file is not None and not os.path.exists(
            self.auto_approve_file
        ):
            raise InvalidArgumentError(f"File {self.auto_approve_file} does not exist")

    def prepare(self):
        self.benchmark = Benchmark.get(self.benchmark_uid)

    def read_and_validate_auto_approve_file(self):
        with open(self.auto_approve_file) as f:
            content = f.read()
        allowed_emails = content.strip().split("\n")
        allowed_emails = [email for email in allowed_emails if email]
        for email in allowed_emails:
            try:
                validate_email(email, check_deliverability=False)
            except EmailNotValidError as e:
                raise InvalidArgumentError(str(e))
        self.allowed_emails = allowed_emails

    def update(self):
        if self.allowed_emails is None and self.auto_approve_mode is None:
            return
        body = {}
        if self.allowed_emails is not None:
            body["association_auto_approval_allow_list"] = self.allowed_emails
        if self.auto_approve_mode is not None:
            body["association_auto_approval_mode"] = self.auto_approve_mode

        config.comms.update_benchmark(self.benchmark_uid, body)
