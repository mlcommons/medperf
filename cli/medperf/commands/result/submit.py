from medperf.utils import pretty_error
from medperf.entities.result import Result
from medperf.entities.dataset import Dataset


class ResultSubmission:
    @classmethod
    def run(cls, benchmark_uid, data_uid, model_uid, comms, ui, approved=False):
        dset = Dataset(data_uid, ui)
        sub = cls(benchmark_uid, dset.uid, model_uid, comms, ui, approved=approved)
        sub.upload_results()

    def __init__(self, benchmark_uid, data_uid, model_uid, comms, ui, approved=False):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = comms
        self.ui = ui
        self.approved = approved

    def upload_results(self):
        result = Result(self.benchmark_uid, self.data_uid, self.model_uid)
        approved = self.approved or result.request_approval(self.ui)

        if not approved:
            msg = "Results upload operation cancelled"
            pretty_error(msg, self.ui, add_instructions=False)

        result.upload(self.comms)
