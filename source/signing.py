import base64
import hashlib
import json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from os.path import exists

# Signs an artifact with private key located at keypath.
def sign(artifact, keypath):
    if not exists(keypath):
        print(f"Private key not found at {keypath}")
        exit(1)
    with open(keypath, 'rb') as pem_in:
        pemlines = pem_in.read()
    private_key = load_pem_private_key(pemlines, None, default_backend())

    artifact_b64 = base64.b64encode(json.dumps(artifact))

    artifact_signature = private_key.sign(
        artifact_b64.encode(),
        ec.ECDSA(hashes.SHA256())
    )

    public_key = private_key.public_key()
    public_key_hash = hashlib.sha256(public_key).hexdigest()

    return {
        "keyid": public_key_hash,
        "keytype": "ecdsa",
        "sig": base64.b64encode(artifact_signature)
    }
