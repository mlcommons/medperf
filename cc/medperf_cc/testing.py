"""Minting real attestation tokens, for testing anything that verifies them.

Part of the package rather than of its tests, because every consumer of this
protocol needs it: the key broker's tests mint tokens to be refused, and anyone
writing their own verifier needs the same. A fake that answered "valid" would
test nothing, since these paths exist in order to reject things.

Nothing on the verification path imports this, and it depends only on
`cryptography`, so it costs nothing to ship.
"""

import base64
import json
import time
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _name(common_name: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])


def _sign_certificate(
    subject, issuer_name, issuer_key, public_key, is_ca, lifetime_days
):
    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer_name)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=lifetime_days))
        .add_extension(
            x509.BasicConstraints(ca=is_ca, path_length=None), critical=True
        )
    )
    return builder.sign(issuer_key, hashes.SHA256())


class FakeAttestationAuthority:
    """A stand-in for Google's attestation service: a root, an intermediate and
    a leaf, able to mint PKI and OIDC tokens."""

    def __init__(self, leaf_lifetime_days: int = 30):
        self.root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.root = _sign_certificate(
            _name("fake attestation root"),
            _name("fake attestation root"),
            self.root_key,
            self.root_key.public_key(),
            is_ca=True,
            lifetime_days=3650,
        )

        self.intermediate_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.intermediate = _sign_certificate(
            _name("fake attestation intermediate"),
            self.root.subject,
            self.root_key,
            self.intermediate_key.public_key(),
            is_ca=True,
            lifetime_days=1825,
        )

        self.leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.leaf = _sign_certificate(
            _name("fake attestation leaf"),
            self.intermediate.subject,
            self.intermediate_key,
            self.leaf_key.public_key(),
            is_ca=False,
            lifetime_days=leaf_lifetime_days,
        )

    @property
    def root_pem(self) -> bytes:
        return self.root.public_bytes(serialization.Encoding.PEM)

    @property
    def jwks(self) -> dict:
        numbers = self.leaf_key.public_key().public_numbers()
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "fake-key-1",
                    "n": b64url(
                        numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
                    ),
                    "e": b64url(
                        numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
                    ),
                }
            ]
        }

    def __x5c(self):
        return [
            base64.b64encode(
                certificate.public_bytes(serialization.Encoding.DER)
            ).decode()
            for certificate in (self.leaf, self.intermediate, self.root)
        ]

    def mint(self, claims: dict, token_type: str = "PKI", signing_key=None) -> str:
        header = {"alg": "RS256", "typ": "JWT"}
        if token_type == "PKI":
            header["x5c"] = self.__x5c()
        else:
            header["kid"] = "fake-key-1"

        signing_input = (
            f"{b64url(json.dumps(header).encode())}."
            f"{b64url(json.dumps(claims).encode())}"
        ).encode()
        key = signing_key or self.leaf_key
        signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        return f"{signing_input.decode()}.{b64url(signature)}"


def confidential_space_claims(**overrides) -> dict:
    """A token body shaped like one Confidential Space issues."""
    now = int(time.time())
    claims = {
        "iss": "https://confidentialcomputing.googleapis.com",
        "aud": "https://relying-party.example.org",
        "iat": now,
        "exp": now + 3600,
        "swname": "CONFIDENTIAL_SPACE",
        "swversion": ["260600"],
        "hwmodel": "GCP_AMD_SEV",
        "dbgstat": "disabled-since-boot",
        "submods": {
            "container": {
                "image_reference": "ghcr.io/example/benchmark-script:1.0",
                "image_digest": "sha256:scripthash",
                "env_override": {
                    "EXPECTED_DATA_HASH": "datahash",
                    "EXPECTED_MODEL_HASH": "modelhash",
                    "EXPECTED_RESULT_COLLECTOR_HASH": "collectorhash",
                },
            },
            "gce": {"zone": "us-west1-b", "project_id": "p", "project_number": "42"},
            "confidential_space": {
                "support_attributes": ["LATEST", "STABLE", "USABLE"]
            },
        },
    }
    # `submods` and `env_override` are nested, so they replace rather than merge.
    env_override = overrides.pop("env_override", None)
    submods = overrides.pop("submods", None)
    claims.update(overrides)
    if env_override is not None:
        claims["submods"]["container"]["env_override"] = env_override
    if submods is not None:
        claims["submods"] = submods
    return claims
