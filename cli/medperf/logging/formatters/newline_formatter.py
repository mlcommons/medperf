# Taken from https://stackoverflow.com/questions/49049044/python-setup-of-logging-allowing-multiline-strings-logging-infofoo-nbar # noqa
import logging


class NewLineFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None):
        """
        Init given the log line format and date format
        """
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record):
        """
        Override format function
        """
        msg = logging.Formatter.format(self, record)

        if record.message != "":
            parts = msg.split(record.message)
            msg = msg.replace("\n", "\n" + parts[0])

        return msg
