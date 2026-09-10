import json
from typing import Callable

import httpx
from tenacity import retry, stop_after_attempt
from tenacity import retry_if_exception, wait_fixed


class BaasException(Exception):
    pass


class AuthException(BaasException):
    pass


class BadRequestException(BaasException):

    def __init__(self, *args):
        super().__init__(*args)
        self.run_id = None
        self.message = None
        try:
            j = json.loads(args[0])
            self.run_id = j["run_id"]
            self.message = j["message"]
        except:
            pass


def is_not_4xx(ex: BaseException) -> bool:
    if isinstance(ex, AuthException):
        return False
    if isinstance(ex, BadRequestException):
        return False
    if not isinstance(ex, httpx.HTTPStatusError):
        return True
    return ex.response.status_code < 400 or ex.response.status_code >= 500


def standard_retry(function: Callable) -> Callable:
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(3),
        reraise=True,
        retry=retry_if_exception(is_not_4xx),
    )(function)
