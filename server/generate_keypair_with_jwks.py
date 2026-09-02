"""Not used. Not tested. Might be useful if we want to test
the server with jwks config (like in production) instead of an explicit public key"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
import base64
import json

# generate keys
private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=4096, backend=default_backend()
)
public_key = private_key.public_key()

# extract public key attributes
n = public_key.public_numbers().n
e = public_key.public_numbers().e

spki = public_key.public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

thumbprint = hashes.Hash(hashes.SHA256(), backend=default_backend())
thumbprint.update(spki)
thumbprint_digest = thumbprint.finalize()

# encode public key attributes
x5c = base64.b64encode(spki).decode("utf-8")
x5t = base64.b64encode(thumbprint_digest).decode("utf-8")
n = (
    base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, byteorder="big"))
    .decode("utf-8")
    .rstrip("=")
)
e = (
    base64.urlsafe_b64encode(e.to_bytes((e.bit_length() + 7) // 8, byteorder="big"))
    .decode("utf-8")
    .rstrip("=")
)

# define the json web key
rsa_json = {
    "kty": "RSA",
    "use": "sig",
    "n": n,
    "e": e,
    "kid": "fwepfng_wegwfnw0230efnw",
    "x5t": x5t,
    "x5c": [x5c],
    "alg": "RS256",
}

# Store keys
jwks = {"keys": [rsa_json]}
with open("jwks.json", "w") as f:
    json.dump(jwks, f)

private_key_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

with open("private_key.pem.test", "wb") as f:
    f.write(private_key_pem)
