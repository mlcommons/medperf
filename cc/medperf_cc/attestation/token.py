"""The claims of a Confidential Space attestation token.

A workload cannot hand over raw hardware evidence: the launcher collects the
attestation report, has a verifier check it, and hands back a signed token. So
everything a policy can require has to be a claim in here.

Two issuers can sign one: Google Cloud Attestation, or Intel Trust Authority for
TDX. Two token types: a PKI token carries its own certificate chain and verifies
against a pinned root; an OIDC token needs the issuer's rotating JWKS.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from medperf_cc.attestation import jws
from medperf_cc.errors import AttestationError

GOOGLE_ISSUER = "https://confidentialcomputing.googleapis.com"
GOOGLE_PKI_ROOT_URL = (
    "https://confidentialcomputing.googleapis.com/.well-known/attestation-pki-root"
)

CONFIDENTIAL_SPACE_SWNAME = "CONFIDENTIAL_SPACE"
STABLE_SUPPORT_ATTRIBUTE = "STABLE"
GPU_CC_MODE_ON = "ON"


class TokenType(Enum):
    PKI = "PKI"
    OIDC = "OIDC"


@dataclass
class AttestationToken:
    """Parsed, not yet verified."""

    raw: str
    header: dict
    claims: dict
    signing_input: bytes
    signature: bytes

    @classmethod
    def parse(cls, raw: str) -> "AttestationToken":
        header, claims, signing_input, signature = jws.split(raw)
        return cls(raw, header, claims, signing_input, signature)

    @property
    def token_type(self) -> TokenType:
        return TokenType.PKI if "x5c" in self.header else TokenType.OIDC

    @property
    def algorithm(self) -> str:
        algorithm = self.header.get("alg")
        if not algorithm or algorithm == "none":
            raise AttestationError("Token does not declare a signing algorithm")
        return algorithm

    @property
    def key_id(self) -> Optional[str]:
        return self.header.get("kid")

    def claim(self, path: str, default=None):
        value = self.claims
        for part in path.split("."):
            if not isinstance(value, dict):
                return default
            value = value.get(part)
        return default if value is None else value

    @property
    def issuer(self) -> Optional[str]:
        return self.claims.get("iss")

    @property
    def issued_at(self) -> Optional[int]:
        return self.claims.get("iat")

    @property
    def expires_at(self) -> Optional[int]:
        return self.claims.get("exp")

    @property
    def audience(self) -> Optional[str]:
        audience = self.claims.get("aud")
        if isinstance(audience, list):
            return audience[0] if audience else None
        return audience

    @property
    def nonces(self) -> List[str]:
        """`eat_nonce` is a string for one nonce and a list for several."""
        nonce = self.claims.get("eat_nonce")
        if nonce is None:
            return []
        return list(nonce) if isinstance(nonce, list) else [nonce]

    @property
    def image_digest(self) -> Optional[str]:
        return self.claim("submods.container.image_digest")

    @property
    def image_reference(self) -> Optional[str]:
        return self.claim("submods.container.image_reference")

    @property
    def env_override(self) -> dict:
        return self.claim("submods.container.env_override", {}) or {}

    @property
    def software_name(self) -> Optional[str]:
        return self.claims.get("swname")

    @property
    def hardware_model(self) -> Optional[str]:
        return self.claims.get("hwmodel")

    @property
    def zone(self) -> Optional[str]:
        return self.claim("submods.gce.zone")

    @property
    def support_attributes(self) -> List[str]:
        return self.claim("submods.confidential_space.support_attributes", []) or []

    @property
    def gpu_cc_mode(self) -> Optional[str]:
        """Whether the GPU ran with its own confidential mode on."""
        return self.claim("submods.nvidia_gpu.cc_mode")

    @property
    def is_debug(self) -> bool:
        """`dbgstat` reads "disabled-since-boot" when debugging is off."""
        return self.claims.get("dbgstat") != "disabled-since-boot"
