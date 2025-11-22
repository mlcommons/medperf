from time import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import jwt
import json

with open("private_key.pem.test", "rb") as f:
    private_key_pem = f.read()

private_key = serialization.load_pem_private_key(
    private_key_pem, password=None, backend=default_backend()
)


def token_payload(user):
    return {
        "https://medperf.org/email": f"{user}@example.com",
        "iss": "https://localhost:8000/",
        "sub": user,
        "aud": "https://localhost-localdev/",
        "iat": int(time()),
        "exp": int(time()) + 10**10,
    }


users = ["testadmin", "testbo", "testmo", "testdo", "testdo2", "testao", "testfladmin", "testpo"]
tokens = {}

# Use headers when verifying tokens using json web keys
# headers = {"alg": "RS256", "typ": "JWT", "kid": "fwepfng_wegwfnw0230efnw"}
headers = None
for user in users:
    tokens[f"{user}@example.com"] = jwt.encode(
        token_payload(user), private_key, algorithm="RS256"
    )

json.dump(tokens, open("tokens.json", "w"))
