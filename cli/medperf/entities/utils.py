from medperf.utils import format_errors_dict
from medperf.exceptions import MedperfException
from pydantic import ValidationError
from collections import defaultdict
import functools


def handle_validation_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            errors_dict = defaultdict(list)
            for error in e.errors():
                field = error["loc"]
                msg = error["msg"]
                errors_dict[field].append(msg)

            error_msg = "Field Validation Error:"
            error_msg += format_errors_dict(errors_dict)

            raise MedperfException(error_msg)

    return wrapper
