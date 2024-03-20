from textual.message import Message


class ReportUpdated(Message):
    def __init__(self, report: dict, highlight: set, dset_path: str):
        self.report = report
        self.highlight = highlight
        self.dset_path = dset_path
        super().__init__()
