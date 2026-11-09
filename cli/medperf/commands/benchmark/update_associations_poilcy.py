import os

import medperf.config as config
from medperf.entities.benchmark import Benchmark
from medperf.enums import AutoApprovalMode
from medperf.exceptions import CleanExit, InvalidArgumentError, MedperfException
from medperf.utils import approval_prompt, sanitize_path, validate_and_normalize_emails


class UpdateAssociationsPolicy:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        dataset_mode: str = None,
        dataset_emails_file: str = None,
        dataset_emails: str = None,
        model_mode: str = None,
        model_emails_file: str = None,
        model_emails: str = None,
        approved: bool = False,
    ):
        """
        dataset_emails: a string containing space-separated list of emails
        model_emails: a string containing space-separated list of emails
        """
        update_policy = cls(
            benchmark_uid,
            dataset_mode,
            dataset_emails_file,
            dataset_emails,
            model_mode,
            model_emails_file,
            model_emails,
            approved,
        )
        update_policy.validate()
        update_policy.read_emails()
        update_policy.validate_emails()
        update_policy.check_empty_allow_lists()
        update_policy.update()

    def __init__(
        self,
        benchmark_uid: int,
        dataset_mode: str = None,
        dataset_emails_file: str = None,
        dataset_emails: str = None,
        model_mode: str = None,
        model_emails_file: str = None,
        model_emails: str = None,
        approved: bool = False,
    ):
        self.benchmark_uid = benchmark_uid
        self.dataset_mode = dataset_mode
        self.dataset_emails_file = sanitize_path(dataset_emails_file)
        self.dataset_emails = dataset_emails
        self.model_mode = model_mode
        self.model_emails_file = sanitize_path(model_emails_file)
        self.model_emails = model_emails
        self.approved = approved

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

    def validate(self):
        # validate modes
        self.dataset_mode = self.__validate_mode(self.dataset_mode)
        self.model_mode = self.__validate_mode(self.model_mode)

        # File and list shouldn't both be provided
        if self.dataset_emails_file is not None and self.dataset_emails is not None:
            raise MedperfException(
                "Internal Error: Both a file and a list of emails are provided."
            )
        if self.model_emails_file is not None and self.model_emails is not None:
            raise MedperfException(
                "Internal Error: Both a file and a list of emails are provided."
            )

        # validate files if provided
        if self.dataset_emails_file and not os.path.isfile(self.dataset_emails_file):
            raise InvalidArgumentError(
                f"File {self.dataset_emails_file} does not exist or is a directory"
            )
        if self.model_emails_file and not os.path.isfile(self.model_emails_file):
            raise InvalidArgumentError(
                f"File {self.dataset_emails_file} does not exist or is a directory"
            )

    def __read_emails_file(self, file):
        with open(file) as f:
            contents = f.read()
        allowed_emails = contents.strip().split("\n")
        return allowed_emails

    def read_emails(self):
        if self.dataset_emails_file is not None:
            self.dataset_emails = self.__read_emails_file(self.dataset_emails_file)
        elif self.dataset_emails is not None:
            self.dataset_emails = self.dataset_emails.strip().split(" ")
        if self.model_emails_file is not None:
            self.model_emails = self.__read_emails_file(self.model_emails_file)
        elif self.model_emails is not None:
            self.model_emails = self.model_emails.strip().split(" ")

    def validate_emails(self):
        if self.dataset_emails is not None:
            self.dataset_emails = validate_and_normalize_emails(self.dataset_emails)
        if self.model_emails is not None:
            self.model_emails = validate_and_normalize_emails(self.model_emails)

    def __empty_allow_list_mode(self, kind, mode, saved_mode, saved_allow_list):
        """Mode to save with an emptied allow list: an empty allow list
        auto-approves nobody, so it is refused if the saved one is already
        empty, otherwise (the user is emptying it) the mode becomes NEVER."""
        if (mode or saved_mode) != "ALLOWLIST":
            return mode
        if not saved_allow_list:
            raise InvalidArgumentError(
                f"The {kind} allow list is empty. Add at least one email, or "
                "choose another auto approve mode."
            )
        msg = (
            f"This will empty the {kind} allow list and set the {kind} auto "
            "approve mode to NEVER. Do you confirm? [Y/n] "
        )
        if not self.approved and not approval_prompt(msg):
            raise CleanExit("Associations policy update cancelled")
        return "NEVER"

    def check_empty_allow_lists(self):
        # None means the list wasn't part of this submission (it stays as is);
        # only an explicitly-submitted empty list ([]) needs checking.
        if self.dataset_emails != [] and self.model_emails != []:
            return
        benchmark = Benchmark.get(self.benchmark_uid)
        if self.dataset_emails == []:
            self.dataset_mode = self.__empty_allow_list_mode(
                "dataset",
                self.dataset_mode,
                benchmark.dataset_auto_approval_mode,
                benchmark.dataset_auto_approval_allow_list,
            )
        if self.model_emails == []:
            self.model_mode = self.__empty_allow_list_mode(
                "model",
                self.model_mode,
                benchmark.model_auto_approval_mode,
                benchmark.model_auto_approval_allow_list,
            )

    def update(self):
        if all(
            [
                self.dataset_emails is None
                and self.model_emails is None
                and self.dataset_mode is None
                and self.model_mode is None
            ]
        ):
            return
        body = {}
        if self.dataset_emails is not None:
            body["dataset_auto_approval_allow_list"] = self.dataset_emails
        if self.model_emails is not None:
            body["model_auto_approval_allow_list"] = self.model_emails
        if self.dataset_mode is not None:
            body["dataset_auto_approval_mode"] = self.dataset_mode
        if self.model_mode is not None:
            body["model_auto_approval_mode"] = self.model_mode

        config.comms.update_benchmark(self.benchmark_uid, body)
