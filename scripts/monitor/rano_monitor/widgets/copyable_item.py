import pyperclip
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.reactive import reactive

class CopyableItem(Static):
    content = reactive("")

    def __init__(self, label: str, content: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(f"{self.label}: ", classes="subject-item-label")
        yield Static(self.content, classes="subject-item-content")
        yield Button("Copy", classes="subject-item-copy")

    def update(self, content):
        self.content = content

    def watch_content(self, content):
        if not isinstance(content, str) or len(content) == 0:
            self.display = False
            return
        subject = self.query_one(".subject-item-content", Static)
        subject.update(content)
        self.display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        try:
            pyperclip.copy(self.content)
            self.notify("Text copied to clipboard")
        except pyperclip.PyperclipException:
            with open("clipboard.txt", "w") as f:
                f.write(self.content)
            self.notify(
                "Clipboard not supported on your machine. Contents copied to clipboard.txt",
                severity="warning",
            )
