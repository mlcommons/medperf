# Taken from https://stackoverflow.com/questions/49049044/python-setup-of-logging-allowing-multiline-strings-logging-infofoo-nbar # noqa
import logging


class NewLineFormatter(logging.Formatter):
    def format(self, record):
        """
        Override format function
        """
        # Apply log formatting
        msg = super().format(record)

        if record.message != "":
            # Separate the logging formatting prefix from the message
            parts = msg.split(record.message)
            # Apply the logging formatting prefix to each newline to retain
            # formatting structure
            msg = msg.replace("\n", "\n" + parts[0])

        return msg
