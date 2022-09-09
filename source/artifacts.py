import json
import os
import sys
import requests
from . import github, signing

def fetch_verified_hashes(owner, repo, token):
    artifact_urls, link_urls = github.fetch_links_from_github(owner, repo, token)

    link_response = requests.get(link_urls["compile"])
    paths = json.loads(link_response.content)["signed"]["products"]
    verified_hashes = []
    for path in paths:
        product_name = os.path.basename(path)
        hash = paths[path]["sha256"]
        product_signing_materials = artifact_urls[product_name]

        sig_response = requests.get(product_signing_materials["sig"])
        crt_response = requests.get(product_signing_materials["crt"])

        if not signing.verify_hash_with_cert(hash, sig_response.content, crt_response.content):
            print("Hash verification failed!")
            sys.exit(1)

        verified_hashes += [hash]

    return verified_hashes
