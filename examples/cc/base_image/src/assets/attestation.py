"""Asking the Confidential Space launcher for an attestation token.

A workload cannot obtain raw hardware evidence: the launcher collects the
attestation report, has it verified, and hands back a signed token. So this is
the only attestation primitive a workload has, and anything that needs to prove
what this workload is goes through here.

Two issuers, chosen by whoever is going to check the token:

- Google Cloud Attestation, at ``/v1/token``
- Intel Trust Authority, at ``/v1/intel/token`` (Intel TDX only)

Prefer ``PKI`` tokens. They carry their own certificate chain, so whoever checks
them needs nothing but a pinned root -- no network, and they keep verifying
after signing keys rotate.
"""

import http.client
import json
import socket
from typing import List, Optional

LAUNCHER_SOCKET = "/run/container_launcher/teeserver.sock"
GOOGLE_TOKEN_PATH = "/v1/token"
INTEL_TOKEN_PATH = "/v1/intel/token"

# Confidential Space accepts at most six nonces, each between 10 and 74 bytes.
MAX_NONCES = 6
MIN_NONCE_LENGTH = 10
MAX_NONCE_LENGTH = 74


class AttestationUnavailable(Exception):
    """The launcher would not issue a token."""


class UnixConnection(http.client.HTTPConnection):
    """HTTP over the launcher's unix domain socket."""

    def __init__(self, socket_path: str, timeout: int = 30):
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


def request_token(
    audience: str,
    nonces: Optional[List[str]] = None,
    token_type: str = "PKI",
    issuer: str = "google",
    socket_path: str = LAUNCHER_SOCKET,
    timeout: int = 30,
) -> str:
    """Returns a signed attestation token carrying `nonces`.

    The nonces are what tie the token to something outside it: a key broker's
    challenge, or the hash of a result. Everything else in the token describes
    the environment, and is filled in by the launcher rather than by us.
    """
    nonces = nonces or []
    __validate_nonces(nonces)

    body = {"audience": audience, "token_type": token_type}
    if nonces:
        body["nonces"] = nonces

    path = INTEL_TOKEN_PATH if issuer == "intel" else GOOGLE_TOKEN_PATH
    connection = UnixConnection(socket_path, timeout=timeout)
    try:
        connection.request(
            "POST",
            path,
            body=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        payload = response.read()
        if response.status != 200:
            raise AttestationUnavailable(
                f"Launcher refused to issue a token ({response.status}): "
                f"{payload.decode(errors='replace')}"
            )
    except OSError as e:
        raise AttestationUnavailable(
            f"Cannot reach the Confidential Space launcher at {socket_path}: {e}"
        )
    finally:
        connection.close()

    return payload.decode().strip()


def __validate_nonces(nonces: List[str]) -> None:
    """Fails here rather than letting the launcher reject the whole request."""
    if len(nonces) > MAX_NONCES:
        raise ValueError(f"At most {MAX_NONCES} nonces are allowed, got {len(nonces)}")
    for nonce in nonces:
        if not MIN_NONCE_LENGTH <= len(nonce.encode()) <= MAX_NONCE_LENGTH:
            raise ValueError(
                f"A nonce must be {MIN_NONCE_LENGTH}-{MAX_NONCE_LENGTH} bytes,"
                f" got {len(nonce.encode())}"
            )
