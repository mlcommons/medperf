"""Verification of Confidential Space attestation tokens."""

from medperf_cc.attestation.authority import AUTHORITIES, GOOGLE, trust_anchor
from medperf_cc.attestation.token import (
    GOOGLE_ISSUER,
    GOOGLE_PKI_ROOT_URL,
    AttestationToken,
    TokenType,
)
from medperf_cc.attestation.verifier import (
    AttestationRequirements,
    TrustAnchor,
    verify_token,
)

__all__ = [
    "AUTHORITIES",
    "GOOGLE",
    "GOOGLE_ISSUER",
    "GOOGLE_PKI_ROOT_URL",
    "AttestationRequirements",
    "AttestationToken",
    "TokenType",
    "TrustAnchor",
    "trust_anchor",
    "verify_token",
]
