"""This module defines a wrapper around the existing token verifier in auth0-python library.
The library is designed to cache public keys in memory. Since our client is ephemeral, we 
wrapped auth0's `JwksFetcher` to cache keys in the filesystem storage, and wrapped auth0's
signature verifier to use this new `JwksFetcher`"""

from typing import Any
from medperf import config
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
        jwk_storage = os.path.join(config.storage, config.auth_jwks_storage)
        if not os.path.exists(jwk_storage):
            return
        with open(jwk_storage) as f:
            data = json.load(f)
        self._cache_value = self._parse_jwks(data["jwks"])
        self._cache_date = data["cache_date"]

    def _cache_jwks(self, jwks: dict[str, Any]) -> None:
        super()._cache_jwks(jwks)
        data = {"cache_date": self._cache_date, "jwks": jwks}
        jwk_storage = os.path.join(config.storage, config.auth_jwks_storage)
        with open(jwk_storage, "w") as f:
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
        config.auth_jwks_url, cache_ttl=config.auth_jwks_cache_ttl
    )
    token_verifier = TokenVerifier(
        signature_verifier=signature_verifier,
        issuer=config.auth_idtoken_issuer,
        audience=config.auth_client_id,
    )
    return token_verifier.verify(token)
