from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.reactive import reactive
from textual.containers import Container, Horizontal

class TarballSubjectView(Static):
    subject = reactive("")
    brain_reviewed = reactive(False)
    tumor_reviewed = reactive(False)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="subject-item"):
            with Container(classes="subject-text"):
                yield Static(self.subject)
                if self.brain_reviewed:
                    yield Static("Brain mask modified")
                if self.tumor_reviewed:
                    yield Static("Tumor segmentation reviewed")

            yield Button("Review Brain Mask", classes="brain-btn")
            yield Button("Review Tumor Segmentation", classes="tumor-btn")