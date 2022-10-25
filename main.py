import argparse, json, sys
from source import artifacts, allowlists

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--owner", help="Github repository owner", action="store")
    parser.add_argument("-r", "--repository", help="Github repository name", action="store")
    parser.add_argument("-t", "--token", help="Github access token", action="store")
    parser.add_argument("-l", "--local_app_path", help="local app path", action="store")
    parser.add_argument("-d", "--destination_app_path", help="destination app path on Keylime target", action="store")
    parser.add_argument("-a", "--allowlist", help="local path of Keylime allowlist", action="store")
    parser.add_argument(
        "-i", "--intoto",
        help="""
            in-toto verification type. Valid options:
            - 'simple'
            - 'default-layout'
            - filepath of existing layout. Also requires -k or --intoto-key
            """,
        action="store"
    )
    parser.add_argument("-k", "--intoto_key", help="filepath of in-toto layout key, used alongside an in-toto layout path provided to -i or --intoto", action="store")
    parser.add_argument("-p", "--intoto_key_password", help="password used with --intoto_key", action="store")
    parser.add_argument("-s", "--sigstore", help="whether to verify inclusion proofs against Sigstore", action="store_true")
    args = parser.parse_args()

    owner = args.owner
    repository = args.repository
    token = args.token
    local_app_path = args.local_app_path
    destination_app_path = args.destination_app_path
    intoto = {
        "layout_path": args.intoto,
        "layout_key": args.intoto_key,
        "layout_key_password": args.intoto_key_password
    }
    sigstore_verify = args.sigstore
    allowlist = args.allowlist
    amended_policy = None

    print("""
     --- SUPPLY CHAIN BRIDGE ---

    This tool will verify an artifact's provenance using publicly-accessible
    supply chain tooling, then forward verified hashes to a Keylime policy.

     --- STEP 1: VERIFY BINARY ---

    """)

    if owner and repository and token:
        verified_hashes = artifacts.fetch_verified_hashes(owner, repository, token, local_app_path, sigstore_verify, intoto)
        print(f"Verified hashes for {owner}/{repository}:")
        for hash in verified_hashes:
            print(hash)
    else:
        print("--owner, --repository, and --token are all required to fetch artifacts from Github")

    print("""

     --- STEP 2: UPDATE KEYLIME POLICY ---

    """)

    if destination_app_path:
        verified_hash = verified_hashes[0]
        print(f"Adding verified hash {verified_hash} to allowlist with destination path {destination_app_path}")
        if allowlist:
            print(f"Using existing allowlist present at {allowlist}")
        amended_policy = allowlists.append_path_to_allowlist(allowlists.get_allowlist(allowlist), destination_app_path, verified_hash)

    if amended_policy:
        with open("keylime-policy.json", "w") as f:
           f.write(json.dumps(amended_policy))
        print("Amended policy written to keylime-policy.json")

    print("""

     --- COMPLETE! ---

    """)

if __name__ == "__main__":
   main()
