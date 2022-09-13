import base64
import hashlib
import json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.exceptions import InvalidSignature
from cryptography.x509 import load_pem_x509_certificate
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

# Verifies provided hash against provided signature using pubkey found in provided certificate.
def verify_hash_with_cert(artifact_raw, sig_raw, crt_raw):
    sig = base64.b64decode(sig_raw)
    crt = load_pem_x509_certificate(crt_raw)

    try:
        crt.public_key().verify(
            sig,
            artifact_raw,
            ec.ECDSA(hashes.SHA256())
        )
        verified = True
    except InvalidSignature:
        print("Signature validation failed!")
        verified = False

    return verified
