from textual.message import Message

class InvalidSubjectsUpdated(Message):
    def __init__(self, invalid_subjects):
        self.invalid_subjects = invalid_subjects
        super().__init__()

