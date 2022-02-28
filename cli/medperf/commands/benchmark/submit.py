import validators

from medperf.ui import UI
from medperf.comms import Comms
from medperf.utils import get_file_sha1


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
            ui.text = "Getting hash from demo dataset"
            submission.get_demo_data_information()
            ui.print("> Completed benchmark registration information")
            ui.text = "Submitting Benchmark to MedPerf"
            submission.submit()
        ui.print("Uploaded")

    def __init__(self, comms: Comms, ui: UI):
        self.comms = comms
        self.ui = ui
        self.name = None
        self.description = None
        self.docs_url = None
        self.demo_url = None
        self.demo_hash = None
        self.demo_uid = None
        self.data_preparation_mlcube = None
        self.reference_model_mlcube = None
        self.data_evaluator_mlcube = None

    def get_information(self):
        name_prompt = "Name: "
        desc_prompt = "Description: "
        docs_url_prompt = "Documentation URL: "
        demo_dset_prompt = "Demo Dataset Tarball URL: "
        prep_uid_prompt = "Data Preparation MLCube UID: "
        model_uid_prompt = "Reference Model MLCube UID: "
        eval_uid_prompt = "Data Evaluator MLCube UID: "
        self.__get_or_print("name", name_prompt)
        self.__get_or_print("description", desc_prompt)
        self.__get_or_print("docs_url", docs_url_prompt)
        self.__get_or_print("demo_url", demo_dset_prompt)
        self.__get_or_print("data_preparation_mlcube", prep_uid_prompt)
        self.__get_or_print("reference_model_mlcube", model_uid_prompt)
        self.__get_or_print("data_evaluator_mlcube", eval_uid_prompt)

    def __get_or_print(self, attr: str, prompt: str):
        """Will print the value stored in the provided attribute. If value is
        None, it will prompt the user with the given prompt.

        Args:
            attr (str): attribute to check and/or write to.
            prompt (str): message to display to the user if value is None.
        """
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
        demo_url_valid = self.demo_url == "" or validators.url(self.demo_url)
        prep_uid_valid = self.data_preparation_mlcube.isdigit()
        model_uid_valid = self.reference_model_mlcube.isdigit()
        eval_uid_valid = self.data_evaluator_mlcube.isdigit()

        valid_tests = [
            ("name", name_valid_length, "Name is invalid"),
            ("description", desc_valid_length, "Description is too long"),
            ("docs_url", docs_url_valid, "Documentation URL is invalid"),
            ("demo_url", demo_url_valid, "Demo Dataset Tarball URL is invalid"),
            (
                "data_preparation_mlcube",
                prep_uid_valid,
                "Data Preparation MLCube UID is invalid",
            ),
            (
                "reference_model_mlcube",
                model_uid_valid,
                "Reference Model MLCube is invalid",
            ),
            (
                "data_evaluator_mlcube",
                eval_uid_valid,
                "Data Evaluator MLCube is invalid",
            ),
        ]

        valid = True
        for attr, test, error_msg in valid_tests:
            if not test:
                valid = False
                setattr(self, attr, None)
                ui.print_error(error_msg)

        return valid

    def get_demo_data_information(self):
        """Retrieves information from the demo dataset, like hash and
        generated uid
        """
        demo_dset_path = self.comms.get_benchmark_demo_dataset(self.demo_url)
        self.demo_hash = get_file_sha1(demo_dset_path)
        # TODO: This depends on the logic of compatibility testing
        # Must be able to run the preparation step with mocked
        # benchmark
        self.demo_uid = "demo_uid"

    def todict(self):
        return {
            "name": self.name,
            "description": self.description,
            "docs_url": self.docs_url,
            "demo_dataset_tarball_url": self.demo_url,
            "demo_dataset_tarball_hash": self.demo_hash,
            "demo_dataset_generated_uid": self.demo_uid,
            "data_preparation_mlcube": int(self.data_preparation_mlcube),
            "reference_model_mlcube": int(self.reference_model_mlcube),
            "data_evaluator_mlcube": int(self.data_evaluator_mlcube),
            "state": "OPERATION",
            "is_valid": True,
            "approval_status": "PENDING",
        }

    def submit(self):
        body = self.todict()
        self.comms.upload_benchmark(body)
