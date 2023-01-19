class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    @property
    def content(self):
        strings = [f"{k}: {v}" for k, v in self.json_data]
        text = "\n".join(strings)
        return text.encode()
