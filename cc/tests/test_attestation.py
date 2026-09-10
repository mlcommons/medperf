import time

import pytest

from medperf_cc.attestation import (
    AttestationRequirements,
    AttestationToken,
    TokenType,
    TrustAnchor,
    verify_token,
)
from medperf_cc.errors import AttestationError
from medperf_cc.testing import FakeAttestationAuthority, confidential_space_claims


@pytest.fixture()
def authority():
    return FakeAttestationAuthority()


@pytest.fixture()
def anchor(authority):
    return TrustAnchor(pki_root_pem=authority.root_pem)


def test_a_genuine_token_verifies_against_the_pinned_root(authority, anchor):
    raw = authority.mint(confidential_space_claims())

    token = verify_token(raw, anchor, AttestationRequirements())

    assert token.token_type is TokenType.PKI
    assert token.claim("submods.container.image_digest") == "sha256:scripthash"


def test_a_token_from_another_authority_is_refused(anchor):
    """The chain is anchored on the pinned root, never on what the token
    supplied, so a self-consistent chain from elsewhere is worth nothing"""
    impostor = FakeAttestationAuthority()
    raw = impostor.mint(confidential_space_claims())

    with pytest.raises(AttestationError):
        verify_token(raw, anchor, AttestationRequirements())


def test_a_tampered_payload_is_refused(authority, anchor):
    raw = authority.mint(confidential_space_claims())
    header, payload, signature = raw.split(".")
    forged = authority.mint(confidential_space_claims(hwmodel="INTEL_TDX"))

    tampered = f"{header}.{forged.split('.')[1]}.{signature}"

    with pytest.raises(AttestationError):
        verify_token(tampered, anchor, AttestationRequirements())


def test_a_token_signed_by_a_key_outside_the_chain_is_refused(authority, anchor):
    other = FakeAttestationAuthority()
    raw = authority.mint(confidential_space_claims(), signing_key=other.leaf_key)

    with pytest.raises(AttestationError):
        verify_token(raw, anchor, AttestationRequirements())


def test_an_expired_token_is_refused(authority, anchor):
    past = int(time.time()) - 7200
    raw = authority.mint(confidential_space_claims(iat=past, exp=past + 3600))

    with pytest.raises(AttestationError, match="expired"):
        verify_token(raw, anchor, AttestationRequirements())


def test_an_oidc_token_needs_a_jwks(authority):
    raw = authority.mint(confidential_space_claims(), token_type="OIDC")

    with pytest.raises(AttestationError, match="no JWKS"):
        verify_token(
            raw,
            TrustAnchor(pki_root_pem=authority.root_pem),
            AttestationRequirements(),
        )


def test_an_oidc_token_verifies_against_a_jwks(authority):
    raw = authority.mint(confidential_space_claims(), token_type="OIDC")
    anchor = TrustAnchor(jwks=authority.jwks)

    assert verify_token(raw, anchor, AttestationRequirements()).token_type is (
        TokenType.OIDC
    )


def test_a_token_type_the_policy_does_not_accept_is_refused(authority):
    raw = authority.mint(confidential_space_claims(), token_type="OIDC")
    anchor = TrustAnchor(jwks=authority.jwks)

    with pytest.raises(AttestationError, match="not accepted"):
        verify_token(
            raw, anchor, AttestationRequirements(allowed_token_types=[TokenType.PKI])
        )


def test_an_unsigned_token_is_refused(authority, anchor):
    """`alg: none` is the oldest JWT trick there is"""
    raw = authority.mint(confidential_space_claims())
    token = AttestationToken.parse(raw)
    token.header["alg"] = "none"

    with pytest.raises(AttestationError, match="signing algorithm"):
        token.algorithm


@pytest.mark.parametrize(
    "overrides,requirements",
    [
        ({"swname": "GCE"}, {}),
        ({"dbgstat": "enabled"}, {}),
        ({}, {"audience": "https://elsewhere"}),
        ({}, {"nonce": "not-in-the-token"}),
        ({}, {"zone": "europe-west4-a"}),
        ({}, {"hardware_model": "INTEL_TDX"}),
    ],
)
def test_an_environment_the_policy_rules_out_is_refused(
    authority, anchor, overrides, requirements
):
    raw = authority.mint(confidential_space_claims(**overrides))

    with pytest.raises(AttestationError):
        verify_token(raw, anchor, AttestationRequirements(**requirements))


def test_a_non_stable_image_is_refused(authority, anchor):
    claims = confidential_space_claims()
    claims["submods"]["confidential_space"]["support_attributes"] = ["LATEST"]
    raw = authority.mint(claims)

    with pytest.raises(AttestationError, match="STABLE"):
        verify_token(raw, anchor, AttestationRequirements())


def test_a_non_stable_image_with_a_confidential_gpu_is_accepted(authority, anchor):
    """What the GCP vault releases a key to, this has to accept a proof from.

    The cGPU images report LATEST but not STABLE, so refusing them here would
    refuse every proof of a GPU run whose key that vault released."""
    claims = confidential_space_claims()
    claims["submods"]["confidential_space"]["support_attributes"] = ["LATEST"]
    claims["submods"]["nvidia_gpu"] = {"cc_mode": "ON"}
    raw = authority.mint(claims)

    verify_token(raw, anchor, AttestationRequirements())


def test_a_non_stable_image_with_the_gpu_mode_off_is_refused(authority, anchor):
    claims = confidential_space_claims()
    claims["submods"]["confidential_space"]["support_attributes"] = ["LATEST"]
    claims["submods"]["nvidia_gpu"] = {"cc_mode": "OFF"}
    raw = authority.mint(claims)

    with pytest.raises(AttestationError, match="STABLE"):
        verify_token(raw, anchor, AttestationRequirements())


def test_a_nonce_the_token_carries_is_accepted(authority, anchor):
    raw = authority.mint(confidential_space_claims(eat_nonce=["first", "second"]))

    verify_token(raw, anchor, AttestationRequirements(nonce="second"))


def test_malformed_input_is_an_attestation_error(anchor):
    with pytest.raises(AttestationError, match="compact serialization"):
        verify_token("not-a-token", anchor, AttestationRequirements())
