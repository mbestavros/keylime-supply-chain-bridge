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
from typing import cast
from .sigstore import merkle, sigstore_shim

from sigstore._verify import (
    CertificateVerificationFailure,
    VerificationFailure,
    Verifier,
)

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

# Verifies provided artifact against provided signature using pubkey found in provided certificate.
def verify_hash_with_cert(artifact_raw, sig_raw, crt_raw):
    sig = base64.b64decode(sig_raw)
    crt = load_pem_x509_certificate(crt_raw)

    try:
        crt.public_key().verify(
            sig,
            artifact_raw,
            ec.ECDSA(hashes.SHA256())
        )
        print("Artifact signature validation passed!")
        verified = True
    except InvalidSignature:
        print("Artifact signature validation failed!")
        verified = False

    return verified

# Verifies provided artifact for inclusion in the Sigstore transparency log.
def verify_inclusion_proof(artifact_raw, sig_raw, crt_raw):
    sig = base64.b64decode(sig_raw)
    pubkey = load_pem_x509_certificate(crt_raw).public_key()
    artifact_hash = hashlib.sha256(artifact_raw).hexdigest()

    search_response = sigstore_shim.search(hash=artifact_hash)
    uuids = json.loads(search_response.content)

    print(f'Found Rekor entries matching provided artifact hash. Verifying...')

    for uuid in uuids:

        fetch_uuid_response = sigstore_shim.fetch_with_uuid(uuid=uuid)

        entries = json.loads(fetch_uuid_response.content)
        for key in entries.keys():
            entry = entries[key]
        encoded_rekord = entry["body"]
        rekor_cert = json.loads(base64.b64decode(encoded_rekord))['spec']['signature']['content']

        valid_signature_found = False
        try:
            pubkey.verify(base64.b64decode(rekor_cert), artifact_raw, ec.ECDSA(hashes.SHA256()))
            print(f'{uuid[:16]}: Rekor signature validation: PASS')
            valid_signature_found = True
        except Exception as e:
            continue

        if valid_signature_found:
            try:
                merkle.verify_merkle_inclusion(entry)
                print("Inclusion proof verified!")
                return True
            except merkle.InvalidInclusionProofError as e:
                print("Inclusion proof failed to verify!")
                print(e)
                return False
        else:
            print("No valid signature was found in any of the fetched Rekor entries!")
            return False

# Verifies provided artifact against Sigstore using the sigstore-python library.
def verify_sigstore_python(artifact_raw, sig_raw, crt_raw):
    verifier = Verifier.production()

    result = verifier.verify(
        input_=artifact_raw,
        certificate=crt_raw,
        signature=sig_raw
    )

    if result:
        return True
    else:
        result = cast(VerificationFailure, result)
        print(f"FAIL")
        print(f"Failure reason: {result.reason}")
        return False
