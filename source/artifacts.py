import hashlib
import json
import os
import sys
import requests
from . import github, signing, intoto_tools

def fetch_verified_hashes(owner, repo, token, local_app_path=None, sigstore_verify=False, experimental=False):
    artifact_urls, link_urls, id_key_urls = github.fetch_links_from_github(owner, repo, token)

    # if local_app_path:
    #     print(f"Verifying local binary at {local_app_path} against signing materials from {owner}/{repo}")
    #     with open(local_app_path, "rb") as f:
    #         artifact_raw = f.read()
    # else:
    #     print(f"Verifying remote binary from {owner}/{repo} against signing materials from {owner}/{repo}")
    #     artifact_raw = requests.get(artifact_signing_materials["artifact"]).content

    # app_binary = hashlib.sha256(artifact_raw).hexdigest()

    link_response = requests.get(link_urls["compile"]["url"])
    paths = json.loads(link_response.content)["signed"]["products"]
    verified_hashes = []
    for path in paths:
        artifact_name = os.path.basename(path)
        hash = paths[path]["sha256"]
        artifact_signing_materials = artifact_urls[artifact_name]

        sig_response = requests.get(artifact_signing_materials["sig"])
        crt_response = requests.get(artifact_signing_materials["crt"])

        if local_app_path and os.path.basename(local_app_path) == artifact_name:
            print(f"Verifying local binary at {local_app_path} against signing materials from {owner}/{repo}")
            with open(local_app_path, "rb") as f:
                artifact_raw = f.read()
        else:
            print(f"Verifying remote binary from {owner}/{repo} against signing materials from {owner}/{repo}")
            artifact_raw = requests.get(artifact_signing_materials["artifact"]).content

        if experimental:
            print("EXPERIMENTAL: Verifying in-toto supply chain layout")
            intoto_tools.verify_layout(artifact_raw, link_urls, id_key_urls)

        if hashlib.sha256(artifact_raw).hexdigest() == hash:
            print(f"Artifact hash matches link file!")
        else:
            print(f"Artifact hash doesn't match link file!")
            sys.exit(1)

        if not signing.verify_hash_with_cert(artifact_raw, sig_response.content, crt_response.content):
            sys.exit(1)

        if sigstore_verify:
            print(f"Verifying presence of valid signature and inclusion proof against Rekor...")
            if signing.verify_inclusion_proof(artifact_raw, sig_response.content, crt_response.content):
                print("Sigstore validation passed!")
            else:
                print("Sigstore validation failed!")
                sys.exit(1)

        verified_hashes += [hash]

    return verified_hashes
