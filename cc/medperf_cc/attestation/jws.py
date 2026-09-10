"""Just enough JWS to verify an attestation token.

Written on `cryptography` rather than a JWT library: a PKI token carries its own
x5c certificate chain, which JWT libraries do not validate, and a verifier that
must work without reaching the issuer should not depend on one that wants to
fetch keys.
"""

import base64
import json
from datetime import datetime, timezone
from typing import List, Optional

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

from medperf_cc.errors import AttestationError

# Confidential Space signs with RS256. The others are listed so that a change of
# algorithm fails loudly rather than being verified with the wrong primitive.
RSA_HASHES = {
    "RS256": hashes.SHA256(),
    "RS384": hashes.SHA384(),
    "RS512": hashes.SHA512(),
}
EC_HASHES = {
    "ES256": hashes.SHA256(),
    "ES384": hashes.SHA384(),
    "ES512": hashes.SHA512(),
}


def b64url_decode(value: str) -> bytes:
    padding_needed = -len(value) % 4
    try:
        return base64.urlsafe_b64decode(value + "=" * padding_needed)
    except Exception as e:
        raise AttestationError(f"Malformed base64url segment: {e}")


def split(token: str):
    """Returns (header, payload, signing input, signature), unverified."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise AttestationError("Not a JWS compact serialization")

    header_b64, payload_b64, signature_b64 = parts
    try:
        header = json.loads(b64url_decode(header_b64))
        payload = json.loads(b64url_decode(payload_b64))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        raise AttestationError(f"Token header or payload is not JSON: {e}")
    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise AttestationError("Token header and payload must be JSON objects")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    return header, payload, signing_input, b64url_decode(signature_b64)


def verify_signature(
    public_key, algorithm: str, signing_input: bytes, signature: bytes
):
    """Raises `AttestationError` unless the signature is valid."""
    try:
        if algorithm in RSA_HASHES:
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise AttestationError(f"{algorithm} needs an RSA key")
            public_key.verify(
                signature, signing_input, padding.PKCS1v15(), RSA_HASHES[algorithm]
            )
        elif algorithm in EC_HASHES:
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise AttestationError(f"{algorithm} needs an EC key")
            public_key.verify(signature, signing_input, ec.ECDSA(EC_HASHES[algorithm]))
        else:
            raise AttestationError(f"Unsupported signing algorithm: {algorithm}")
    except InvalidSignature:
        raise AttestationError("Token signature is not valid")


def certificate_chain(header: dict) -> List[x509.Certificate]:
    """The `x5c` chain of a PKI token, leaf first."""
    chain_b64 = header.get("x5c")
    if not chain_b64:
        raise AttestationError("Token header carries no x5c certificate chain")

    chain = []
    for entry in chain_b64:
        try:
            # x5c is base64 (not base64url) DER, per RFC 7515.
            chain.append(x509.load_der_x509_certificate(base64.b64decode(entry)))
        except Exception as e:
            raise AttestationError(f"Malformed certificate in x5c chain: {e}")
    return chain


def verify_chain(
    chain: List[x509.Certificate],
    root: x509.Certificate,
    allow_expired: bool = False,
):
    """Verifies a leaf-first chain up to a pinned root.

    `allow_expired` is for checking a proof of a run that already happened. The
    leaf's validity window says when the token was signed, which the token's own
    `iat` already records, so treating an expired leaf as fatal would make every
    proof self-destruct after an hour. Anything authenticating a *live* workload
    must leave it alone."""
    if not chain:
        raise AttestationError("Empty certificate chain")

    # The root may or may not be repeated at the end of x5c. Either way the
    # chain is anchored on the pinned copy, never on what the token supplied.
    full_chain = list(chain)
    if full_chain[-1].fingerprint(hashes.SHA256()) != root.fingerprint(
        hashes.SHA256()
    ):
        full_chain.append(root)
    else:
        full_chain[-1] = root

    for certificate, issuer in zip(full_chain, full_chain[1:]):
        if certificate.issuer != issuer.subject:
            raise AttestationError(
                "Broken certificate chain: "
                f"{certificate.subject.rfc4514_string()} is not issued by "
                f"{issuer.subject.rfc4514_string()}"
            )
        try:
            certificate.verify_directly_issued_by(issuer)
        except Exception as e:
            raise AttestationError(f"Certificate chain does not verify: {e}")

    if allow_expired:
        return

    now = datetime.now(timezone.utc)
    for certificate in full_chain:
        if not (
            certificate.not_valid_before_utc <= now <= certificate.not_valid_after_utc
        ):
            raise AttestationError(
                f"Certificate {certificate.subject.rfc4514_string()} is not valid now"
            )


def load_root(pem: bytes) -> x509.Certificate:
    try:
        return x509.load_pem_x509_certificate(pem)
    except Exception as e:
        raise AttestationError(f"Could not read the pinned root certificate: {e}")


def jwks_public_key(jwks: dict, kid: Optional[str]):
    """The JWKS key matching `kid`, as a public key object."""
    keys = jwks.get("keys") or []
    if kid is not None:
        keys = [key for key in keys if key.get("kid") == kid] or keys
    if not keys:
        raise AttestationError(f"No JWKS key matches kid {kid!r}")

    key = keys[0]
    if key.get("kty") != "RSA":
        raise AttestationError(f"Unsupported JWKS key type: {key.get('kty')}")
    try:
        numbers = rsa.RSAPublicNumbers(
            e=int.from_bytes(b64url_decode(key["e"]), "big"),
            n=int.from_bytes(b64url_decode(key["n"]), "big"),
        )
        return numbers.public_key()
    except Exception as e:
        raise AttestationError(f"Malformed JWKS key: {e}")
