import getopt, json, sys
from source import artifacts, allowlists

def main(argv):
    owner = None
    repository = None
    token = None
    destination = None
    allowlist = None
    amended_policy = None
    try:
        opts, _ = getopt.getopt(argv,"ho:r:t:p:a:",["owner=", "repository=", "token=", "app-path=", "allowlist="])
    except getopt.GetoptError:
        print('main.py OPTIONS')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("main.py -o <repository owner> -r <repository name> -t <Github access token> -p <app destination path on Keylime target> -a <local path of Keylime allowlist>")
            sys.exit()
        elif opt in ("-o", "--owner"):
            owner = arg
        elif opt in ("-r", "--repository"):
            repository = arg
        elif opt in ("-t", "--token"):
            token = arg
        elif opt in ("-p", "--app-path"):
            destination = arg
        elif opt in ("-a", "--allowlist"):
            allowlist = arg

    if owner and repository and token:
        verified_hashes = artifacts.fetch_verified_hashes(owner, repository, token)
        print(f"Verified hashes for {owner}/{repository}: {verified_hashes}")
    else:
        print("--owner, --repository, and --token are all required to fetch artifacts from Github")
    if destination:
        verified_hash = verified_hashes[0]
        print(f"Adding verified hash {verified_hash} to allowlist with destination path {destination}")
        if allowlist:
            print(f"Using existing allowlist present at {allowlist}")
        amended_policy = allowlists.append_path_to_allowlist(allowlists.get_allowlist(allowlist), destination, verified_hash)

    if amended_policy:
        with open("keylime-policy.json", "w") as f:
           f.write(json.dumps(amended_policy))
        print("Amended policy written to keylime-policy.json")

if __name__ == "__main__":
   main(sys.argv[1:])
