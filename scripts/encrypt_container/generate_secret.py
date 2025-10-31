import secrets
import os

file = "./secret.txt"
with open(file, "wb") as f:
    pass
os.chmod(file, 0o700)
with open(file, "ab") as f:
    f.write(secrets.token_bytes(32))
