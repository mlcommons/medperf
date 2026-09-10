"""The services whose word we take that an attestation is genuine.

A caller names one; getting from that name to a trust anchor is this module's
business. Adding Intel Trust Authority later is adding an entry here, with
nothing outside this package to change.

Fetching a root is deliberately not something `verifier` does: a verifier that
fetches its own trust anchor while verifying is not verifying anything. Whoever
needs one asks for it here, once, and hands it over.
"""

import json
from dataclasses import dataclass
from typing import Optional

import requests

from medperf_cc.attestation.token import (
    GOOGLE_ISSUER,
    GOOGLE_PKI_ROOT_URL,
)
from medperf_cc.attestation.verifier import TrustAnchor
from medperf_cc.errors import AttestationError

GOOGLE = "google"


@dataclass(frozen=True)
class Authority:
    """Who signs an attestation, and where its root certificate comes from."""

    issuer: str
    pki_root_url: str

    def fetch_pki_root(self, timeout: int) -> bytes:
        """The root certificate, in PEM, however this authority publishes it.

        Google's well-known document is the PEM itself or a JSON pointer to it,
        `{"root_ca_uri": "..."}`. One redirection, never a chain of them.
        """
        body = self._get(self.pki_root_url, timeout)
        pointed_at = self._root_ca_uri(body)
        if pointed_at is None:
            return body
        return self._get(pointed_at, timeout)

    @staticmethod
    def _get(url: str, timeout: int) -> bytes:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content

    @staticmethod
    def _root_ca_uri(body: bytes) -> Optional[str]:
        """Where a pointer document points, or None if this is the PEM itself."""
        if body.lstrip().startswith(b"-----BEGIN"):
            return None
        try:
            pointer = json.loads(body)
        except ValueError:
            return None
        uri = pointer.get("root_ca_uri") if isinstance(pointer, dict) else None
        if not isinstance(uri, str) or not uri:
            return None
        # Over plaintext the certificate is anybody's to replace.
        if not uri.startswith("https://"):
            raise ValueError(
                f"{GOOGLE_PKI_ROOT_URL} points at a root certificate over"
                f" something other than https: {uri}"
            )
        return uri


AUTHORITIES = {
    GOOGLE: Authority(issuer=GOOGLE_ISSUER, pki_root_url=GOOGLE_PKI_ROOT_URL),
}


def trust_anchor(authority: str = GOOGLE, timeout: int = 30) -> TrustAnchor:
    """What to accept as proof that a token this authority signed is genuine.

    Fetched now rather than pinned on disk. Pinning buys offline verification,
    which is worth it for something authenticating live workloads all day -- see
    the key broker -- and not for checking a result, which happens rarely and
    only ever with a network."""
    known = AUTHORITIES.get(authority)
    if known is None:
        raise AttestationError(
            f"Unknown attestation authority {authority!r}."
            f" Supported: {', '.join(sorted(AUTHORITIES))}"
        )

    try:
        return TrustAnchor(
            pki_root_pem=known.fetch_pki_root(timeout), expected_issuer=known.issuer
        )
    except Exception as e:
        raise AttestationError(
            f"Could not fetch the root certificate of {authority}: {e}"
        )
