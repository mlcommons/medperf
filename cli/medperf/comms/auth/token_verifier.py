"""This module defines a wrapper around the existing token verifier in auth0-python library.
The library is designed to cache public keys in memory. Since our client is ephemeral, we
wrapped the library's `JwksFetcher` to cache keys in the filesystem storage, and wrapped the
library's signature verifier to use this new `JwksFetcher`"""

from typing import Any
from medperf import settings
import os
import json
from auth0.authentication.token_verifier import (
    TokenVerifier,
    JwksFetcher,
    AsymmetricSignatureVerifier,
)


class JwksFetcherWithDiskCache(JwksFetcher):
    def _init_cache(self, cache_ttl: int) -> None:
        super()._init_cache(cache_ttl)
        jwks_file = settings.auth_jwks_file
        if not os.path.exists(jwks_file):
            return
        with open(jwks_file) as f:
            data = json.load(f)
        self._cache_value = self._parse_jwks(data["jwks"])
        self._cache_date = data["cache_date"]

    def _cache_jwks(self, jwks: dict[str, Any]) -> None:
        super()._cache_jwks(jwks)
        data = {"cache_date": self._cache_date, "jwks": jwks}
        jwks_file = settings.auth_jwks_file
        with open(jwks_file, "w") as f:
            json.dump(data, f)


class AsymmetricSignatureVerifierWithDiskCache(AsymmetricSignatureVerifier):
    def __init__(
        self,
        jwks_url: str,
        algorithm: str = "RS256",
        cache_ttl: int = JwksFetcher.CACHE_TTL,
    ) -> None:
        super().__init__(jwks_url, algorithm, cache_ttl)
        self._fetcher = JwksFetcherWithDiskCache(jwks_url, cache_ttl)


def verify_token(token):
    signature_verifier = AsymmetricSignatureVerifierWithDiskCache(
        settings.auth_jwks_url, cache_ttl=settings.auth_jwks_cache_ttl
    )
    token_verifier = TokenVerifier(
        signature_verifier=signature_verifier,
        issuer=settings.auth_idtoken_issuer,
        audience=settings.auth_client_id,
    )
    return token_verifier.verify(token)
