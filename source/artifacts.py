import json
import os
import sys
import requests
from . import github, signing

def fetch_verified_hashes(owner, repo, token, local_app_path=None):
    artifact_urls, link_urls = github.fetch_links_from_github(owner, repo, token)

    link_response = requests.get(link_urls["compile"])
    paths = json.loads(link_response.content)["signed"]["products"]
    verified_hashes = []
    for path in paths:
        artifact_name = os.path.basename(path)
        hash = paths[path]["sha256"]
        artifact_signing_materials = artifact_urls[artifact_name]

        sig_response = requests.get(artifact_signing_materials["sig"])
        crt_response = requests.get(artifact_signing_materials["crt"])

        if local_app_path and os.path.basename(local_app_path) == artifact_name:
            print(f"Verifying local binary at {local_app_path} against signing materials from Github")
            with open(local_app_path, "rb") as f:
                artifact_raw = f.read()
        else:
            print(f"Verifying remote binary from Github against signing materials from Github")
            artifact_raw = requests.get(artifact_signing_materials["artifact"]).content

        if not signing.verify_hash_with_cert(artifact_raw, sig_response.content, crt_response.content):
            print("Binary signature verification failed!")
            sys.exit(1)

        verified_hashes += [hash]

    return verified_hashes
