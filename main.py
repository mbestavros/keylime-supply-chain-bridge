import getopt, json, sys
from source import artifacts, allowlists

def main(argv):
    owner = None
    repository = None
    token = None
    local_app_path = None
    destination_app_path = None
    sigstore_verify = False
    experimental = False
    allowlist = None
    amended_policy = None
    try:
        opts, _ = getopt.getopt(argv,"ho:r:t:l:d:a:se",["owner=", "repository=", "token=", "local-app-path=", "destination-app-path", "allowlist=", "sigstore", "experimental"])
    except getopt.GetoptError:
        print('main.py OPTIONS')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("main.py -o <repository owner> -r <repository name> -t <Github access token> -l <local app path> -d <destination app path on Keylime target> -a <local path of Keylime allowlist> -s <whether to verify inclusion proofs against Sigstore> -e <enable experimental verification options>")
            sys.exit()
        elif opt in ("-o", "--owner"):
            owner = arg
        elif opt in ("-r", "--repository"):
            repository = arg
        elif opt in ("-t", "--token"):
            token = arg
        elif opt in ("-l", "--local-app-path"):
            local_app_path = arg
        elif opt in ("-d", "--destination-app-path"):
            destination_app_path = arg
        elif opt in ("-a", "--allowlist"):
            allowlist = arg
        elif opt in ("-s", "--sigstore"):
            sigstore_verify = True
        elif opt in ("-e", "--experimental"):
            experimental = True

    if owner and repository and token:
        verified_hashes = artifacts.fetch_verified_hashes(owner, repository, token, local_app_path, sigstore_verify, experimental)
        print(f"Verified hashes for {owner}/{repository}:")
        for hash in verified_hashes:
            print(hash)
    else:
        print("--owner, --repository, and --token are all required to fetch artifacts from Github")
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

if __name__ == "__main__":
   main(sys.argv[1:])
