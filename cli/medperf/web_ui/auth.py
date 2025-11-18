import binascii
import os
from typing import Callable

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

security_token = binascii.hexlify(os.urandom(24)).decode("ascii")
AUTH_COOKIE_NAME = "auth_token"
API_KEY_NAME = "access_token"


class NotAuthenticatedException(Exception):
    def __init__(self, redirect_url: str):
        self.redirect_url = redirect_url


def wrap_openapi(app: FastAPI) -> Callable:
    def _custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Your API",
            version="1.0.0",
            description="API description",
            routes=app.routes,
        )
        api_key_scheme = {"type": "apiKey", "name": API_KEY_NAME, "in": "header"}
        openapi_schema["components"]["securitySchemes"] = {
            "APIKeyHeader": api_key_scheme
        }
        for path in openapi_schema["paths"]:
            for method in openapi_schema["paths"][path]:
                if "security" in openapi_schema["paths"][path][method]:
                    openapi_schema["paths"][path][method]["security"].append(
                        {"APIKeyHeader": []}
                    )
                else:
                    openapi_schema["paths"][path][method]["security"] = [
                        {"APIKeyHeader": []}
                    ]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return _custom_openapi
