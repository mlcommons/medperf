"""Mock identity provider for the local-auth dev configs.

Real deployments get their tokens from the auth provider; locally the server
mints them itself, so the CLI only ever consumes credentials. Everything lands
in ~/.medperf_dev, which the CLI's `local`/`testauth` profiles read from.
"""

import json
import os
from pathlib import Path
from time import time

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

DEV_DIR = Path.home() / ".medperf_dev"
KEYS_DIR = DEV_DIR / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "private_key.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "public_key.pem"
TOKENS_PATH = DEV_DIR / "mock_tokens" / "tokens.json"

USERS = [
    "testadmin",
    "testbo",
    "testmo",
    "testdo",
    "testdo2",
    "testao",
    "testfladmin",
    "testpo",
]


def _generate_keypair() -> None:
    """Writes a fresh RSA keypair. settings.py reads the public half through
    AUTH_VERIFYING_KEY_FILE."""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=4096, backend=default_backend()
    )
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_KEY_PATH.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    os.chmod(PRIVATE_KEY_PATH, 0o600)
    PUBLIC_KEY_PATH.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def _sign_tokens() -> None:
    """Signs a long-lived access token per mock user, for the CLI to log in with."""
    private_key = serialization.load_pem_private_key(
        PRIVATE_KEY_PATH.read_bytes(), password=None, backend=default_backend()
    )
    issued_at = int(time())
    tokens = {
        f"{user}@example.com": jwt.encode(
            {
                "https://medperf.org/email": f"{user}@example.com",
                "iss": "https://localhost:8000/",
                "sub": user,
                "aud": "https://localhost-localdev/",
                "iat": issued_at,
                "exp": issued_at + 10**10,
            },
            private_key,
            algorithm="RS256",
        )
        for user in USERS
    }
    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(json.dumps(tokens))


def ensure_mock_credentials() -> None:
    """Generates the keypair and mock tokens if they aren't there yet."""
    generated_keypair = False
    if not (PRIVATE_KEY_PATH.is_file() and PUBLIC_KEY_PATH.is_file()):
        _generate_keypair()
        generated_keypair = True

    # Tokens signed with a superseded key would be rejected by the server
    if generated_keypair or not TOKENS_PATH.is_file():
        _sign_tokens()

    print(f"Mock login credentials ready under {DEV_DIR}")
