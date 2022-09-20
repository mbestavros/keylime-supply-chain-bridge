import hashlib
import json
import os
import sys
import requests
from . import github, signing, intoto_tools

def fetch_verified_hashes(owner, repo, token, local_app_path=None, sigstore_verify=False, intoto=None):
    artifact_urls, link_urls, id_key_urls = github.fetch_links_from_github(owner, repo, token)

    binaries = {}
    verified_hashes = []
    for artifact_name in artifact_urls.keys():
        artifact_signing_materials = artifact_urls[artifact_name]
        if local_app_path and os.path.basename(local_app_path) == artifact_name:
            print(f"{artifact_name}: Verifying local binary at {local_app_path} against signing materials from {owner}/{repo}")
            with open(local_app_path, "rb") as f:
                artifact_raw = f.read()
        else:
            print(f"{artifact_name}: Verifying remote binary from {owner}/{repo} against signing materials from {owner}/{repo}")
            artifact_raw = requests.get(artifact_signing_materials["artifact"]).content

        sig_response = requests.get(artifact_signing_materials["sig"])
        crt_response = requests.get(artifact_signing_materials["crt"])

        if not signing.verify_hash_with_cert(artifact_raw, sig_response.content, crt_response.content):
            sys.exit(1)

        if sigstore_verify:
            print(f"Verifying presence of valid signature and inclusion proof against Rekor...")
            if signing.verify_inclusion_proof(artifact_raw, sig_response.content, crt_response.content):
                print("Sigstore validation passed!")
            else:
                print("Sigstore validation failed!")
                sys.exit(1)

        binaries[artifact_name] = artifact_raw

    if intoto:
        if intoto["layout_path"] == "simple":
            print("Performing simple in-toto linkfile verification")
            link_response = requests.get(link_urls["compile"]["url"])
            paths = json.loads(link_response.content)["signed"]["products"]
            link_hashes = [paths[p]["sha256"] for p in paths]
            for binary in binaries.values():
                binary_hash = hashlib.sha256(binary).hexdigest()
                if binary_hash in link_hashes:
                    verified_hashes += [binary_hash]
        else:
            print("EXPERIMENTAL: Verifying full in-toto supply chain layout")
            if intoto["layout_path"] != "default-layout":
                print(f"Using in-toto layout definition at {intoto['layout_path']}")
            try:
                intoto_tools.verify_layout(binaries, link_urls, id_key_urls, intoto)
            except Exception as e:
                print(f"in-toto verification failed! Exception: {e}")
                sys.exit(1)

            verified_hashes += [hashlib.sha256(b).hexdigest() for b in binaries.values()]
    else:
        print("WARNING: `-i` or `--intoto` not supplied, skipping in-toto verification")
        verified_hashes += [hashlib.sha256(b).hexdigest() for b in binaries.values()]

    return verified_hashes
