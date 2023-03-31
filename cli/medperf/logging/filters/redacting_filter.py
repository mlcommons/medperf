# Code taken from https://gist.github.com/fredrikaverpil/79ab394b449f29685c89c736c1ac6d67
import logging
import re


class RedactingFilter(logging.Filter):
    def __init__(self, patterns):
        super(RedactingFilter, self).__init__()
        self._patterns = patterns

    def filter(self, record):
        record.msg = self.redact(record.msg)
        if isinstance(record.args, dict):
            for k in record.args.keys():
                record.args[k] = self.redact(record.args[k])
        else:
            record.args = tuple(self.redact(arg) for arg in record.args)
        return True

    def redact(self, msg):
        for pattern in self._patterns:
            msg = re.sub(pattern, "\g<1>[redacted]", str(msg))
        return msg
