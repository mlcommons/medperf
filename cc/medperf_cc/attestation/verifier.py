"""Verifying a token: is it genuine, and does it say what we require.

`TrustAnchor` answers the first question and `AttestationRequirements` the
second. Neither reaches the network: a verifier that fetches its own trust
anchor while verifying is not verifying anything.
"""

import json
import time
from dataclasses import dataclass, field
from typing import List, Optional

from medperf_cc.attestation import jws
from medperf_cc.attestation.token import (
    CONFIDENTIAL_SPACE_SWNAME,
    GOOGLE_ISSUER,
    GPU_CC_MODE_ON,
    STABLE_SUPPORT_ATTRIBUTE,
    AttestationToken,
    TokenType,
)
from medperf_cc.errors import AttestationError


@dataclass
class TrustAnchor:
    """What we are willing to accept as proof that a token is genuine.

    Prefer a PKI root: it is pinned once, it needs no network, and it keeps
    working after the issuer rotates signing keys. A JWKS is accepted for OIDC
    tokens, but a verifier that must work offline should not rely on one.
    """

    pki_root_pem: Optional[bytes] = None
    jwks: Optional[dict] = None
    expected_issuer: Optional[str] = GOOGLE_ISSUER

    @classmethod
    def from_pki_root_file(cls, path: str, expected_issuer: str = GOOGLE_ISSUER):
        with open(path, "rb") as f:
            return cls(pki_root_pem=f.read(), expected_issuer=expected_issuer)

    @classmethod
    def from_jwks_file(cls, path: str, expected_issuer: str = GOOGLE_ISSUER):
        with open(path) as f:
            return cls(jwks=json.load(f), expected_issuer=expected_issuer)

    def verify_signature(self, token: AttestationToken, allow_expired_chain=False):
        if token.token_type is TokenType.PKI:
            self.__verify_pki(token, allow_expired_chain)
        else:
            self.__verify_oidc(token)

        if self.expected_issuer and token.issuer != self.expected_issuer:
            raise AttestationError(
                f"Token issuer {token.issuer!r} is not {self.expected_issuer!r}"
            )

    def __verify_pki(self, token: AttestationToken, allow_expired_chain: bool):
        if not self.pki_root_pem:
            raise AttestationError(
                "Token is a PKI token but no root certificate is pinned"
            )
        chain = jws.certificate_chain(token.header)
        jws.verify_chain(
            chain, jws.load_root(self.pki_root_pem), allow_expired=allow_expired_chain
        )
        jws.verify_signature(
            chain[0].public_key(), token.algorithm, token.signing_input, token.signature
        )

    def __verify_oidc(self, token: AttestationToken):
        if not self.jwks:
            raise AttestationError(
                "Token is an OIDC token but no JWKS is available to verify it."
                " Request a PKI token to verify without contacting the issuer."
            )
        public_key = jws.jwks_public_key(self.jwks, token.key_id)
        jws.verify_signature(
            public_key, token.algorithm, token.signing_input, token.signature
        )


@dataclass
class AttestationRequirements:
    """What the environment must have been for a token to be acceptable."""

    audience: Optional[str] = None
    nonce: Optional[str] = None
    allowed_token_types: List[TokenType] = field(
        default_factory=lambda: [TokenType.PKI, TokenType.OIDC]
    )
    require_confidential_space: bool = True
    require_hardened_image: bool = True
    allow_debug: bool = False
    zone: Optional[str] = None
    hardware_model: Optional[str] = None
    # Authenticating a live workload cares that its token has not expired.
    # Checking a proof written months ago does not: `iat` is then the record of
    # when the run happened, and a one-hour token that had to still be current
    # would make every proof self-destruct.
    check_expiry: bool = True
    clock_skew_seconds: int = 60

    def check(self, token: AttestationToken):
        self.__check_binding(token)
        self.__check_environment(token)
        if self.check_expiry:
            self.__check_expiry(token)

    def __check_binding(self, token: AttestationToken):
        """What ties this token to this exchange rather than any other."""
        if token.token_type not in self.allowed_token_types:
            allowed = ", ".join(t.value for t in self.allowed_token_types)
            raise AttestationError(
                f"Token type {token.token_type.value} is not accepted"
                f" (allowed: {allowed})"
            )

        if self.audience is not None and token.audience != self.audience:
            raise AttestationError(
                f"Token audience {token.audience!r} is not {self.audience!r}"
            )

        if self.nonce is not None and self.nonce not in token.nonces:
            raise AttestationError("Token does not carry the expected nonce")

    @staticmethod
    def __is_hardened(token: AttestationToken) -> bool:
        """A production image, or a GPU vouching for itself.

        The same disjunction the GCP vault installs on its pool provider: the
        cGPU images do not report STABLE yet, so requiring it here would refuse
        every proof of a run whose key that vault released.
        """
        return (
            STABLE_SUPPORT_ATTRIBUTE in token.support_attributes
            or token.gpu_cc_mode == GPU_CC_MODE_ON
        )

    def __check_environment(self, token: AttestationToken):
        """What the workload must have been running in."""
        if (
            self.require_confidential_space
            and token.software_name != CONFIDENTIAL_SPACE_SWNAME
        ):
            raise AttestationError(
                f"Token reports swname {token.software_name!r}; the workload did"
                " not run in Confidential Space"
            )

        if self.require_hardened_image and not self.__is_hardened(token):
            raise AttestationError(
                "Token reports neither a STABLE Confidential Space image nor a"
                " GPU in confidential mode"
            )

        if not self.allow_debug and token.is_debug:
            raise AttestationError("Token reports a debuggable environment")

        if self.zone is not None and token.zone != self.zone:
            raise AttestationError(
                f"Workload ran in zone {token.zone!r}, not {self.zone!r}"
            )

        if (
            self.hardware_model is not None
            and token.hardware_model != self.hardware_model
        ):
            raise AttestationError(
                f"Workload ran on {token.hardware_model!r},"
                f" not {self.hardware_model!r}"
            )

    def __check_expiry(self, token: AttestationToken):
        now = int(time.time())
        if (
            token.expires_at is not None
            and now > token.expires_at + self.clock_skew_seconds
        ):
            raise AttestationError("Token has expired")
        if (
            token.issued_at is not None
            and token.issued_at > now + self.clock_skew_seconds
        ):
            raise AttestationError("Token is issued in the future")


def verify_token(
    raw_token: str, anchor: TrustAnchor, requirements: AttestationRequirements
) -> AttestationToken:
    """Verifies a token and returns it, or raises `AttestationError`.

    The certificate chain is allowed to have expired exactly when the caller has
    stopped caring about token expiry: both mean "this is a historical record,
    not a live authentication"."""
    token = AttestationToken.parse(raw_token)
    anchor.verify_signature(token, allow_expired_chain=not requirements.check_expiry)
    requirements.check(token)
    return token
