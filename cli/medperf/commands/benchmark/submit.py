import validators

from medperf.ui import UI
from medperf.comms import Comms


class SubmitBenchmark:
    @classmethod
    def run(cls, comms: Comms, ui: UI):
        """Submits a new cube to the medperf platform
        Args:
            comms (Comms): Communication instance
            ui (UI): UI instance
        """
        submission = cls(comms, ui)
        submission.get_information()
        while not submission.is_valid():
            submission.get_information()

        with ui.interactive():
            ui.text = "Submitting Benchmark to MedPerf"
            submission.submit()
        ui.print("Uploaded")

    def __init__(self, comms: Comms, ui: UI):
        self.comms = comms
        self.ui = ui
        self.name = None
        self.description = None
        self.docs_url = None
        self.data_preparation_mlcube = None
        self.reference_model_mlcube = None
        self.data_evaluator_mlcube = None

    def get_information(self):
        name_prompt = "Name: "
        desc_prompt = "Description: "
        docs_url_prompt = "Documentation URL: "
        prep_uid_prompt = "Data Preparation MLCube UID: "
        model_uid_prompt = "Reference Model MLCube UID: "
        eval_uid_prompt = "Data Evaluator MLCube UID: "
        self.__get_or_print("name", name_prompt)
        self.__get_or_print("description", desc_prompt)
        self.__get_or_print("docs_url", docs_url_prompt)
        self.__get_or_print("data_preparation_mlcube", prep_uid_prompt)
        self.__get_or_print("reference_model_mlcube", model_uid_prompt)
        self.__get_or_print("data_evaluator_mlcube", eval_uid_prompt)

    def __get_or_print(self, attr, prompt):
        attr_val = getattr(self, attr)
        if attr_val is None or attr_val == "":
            setattr(self, attr, self.ui.prompt(prompt))
        else:
            self.ui.print(prompt + attr_val)

    def is_valid(self) -> bool:
        """Validates that user-provided benchmark information is correct

        Returns:
            bool: Wether or not the benchmark information is valid
        """
        name_valid_length = 0 < len(self.name) < 20
        desc_valid_length = len(self.description) < 100
        docs_url_valid = self.docs_url == "" or validators.url(self.docs_url)
        prep_uid_valid = self.data_preparation_mlcube.isdigit()
        model_uid_valid = self.reference_model_mlcube.isdigit()
        eval_uid_valid = self.data_evaluator_mlcube.isdigit()

        valid = True
        if not name_valid_length:
            valid = False
            self.name = None
            self.ui.print_error("Name is invalid")
        if not desc_valid_length:
            valid = False
            self.description = None
            self.ui.print_error("Description is too long")
        if not docs_url_valid:
            valid = False
            self.docs_url = None
            self.ui.print_error("Documentation URL is invalid")
        if not prep_uid_valid:
            valid = False
            self.data_preparation_mlcube = None
            self.ui.print_error("Data Preparation MLCube UID is invalid")
        if not model_uid_valid:
            valid = False
            self.reference_model_mlcube = None
            self.ui.print_error("Reference Model MLCube is invalid")
        if not eval_uid_valid:
            valid = False
            self.data_evaluator_mlcube = None
            self.ui.print_error("Data Evaluator MLCube is invalid")

        return valid

    def todict(self):
        return {
            "name": self.name,
            "description": self.description,
            "docs_url": self.docs_url,
            "data_preparation_mlcube": int(self.data_preparation_mlcube),
            "reference_model_mlcube": int(self.reference_model_mlcube),
            "data_evaluator_mlcube": int(self.data_evaluator_mlcube),
            "state": "OPERATION",
            "is_valid": True,
            "approval_status": "APPROVED",
        }

    def submit(self):
        body = self.todict()
        self.comms.upload_benchmark(body)
