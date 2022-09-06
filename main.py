import getopt, json, sys
from source import importer, intoto_tools

def main(argv):
    allowlist_path = None
    excludelist_path = None
    keypath = None
    link_path = None
    policy = None
    try:
        opts, _ = getopt.getopt(argv,"ha:e:k:l:",["allowlistfile=", "excludelistfile=", "linkfile="])
    except getopt.GetoptError:
        print('main.py OPTIONS')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("test.py -a <allowlist file> -e <exclude list file> -k <private key file> -l <in-toto link file>")
            sys.exit()
        elif opt in ("-a", "--allowlistfile"):
            allowlist_path = arg
        elif opt in ("-e", "--excludelistfile"):
            excludelist_path = arg
        elif opt in ("-k", "--keyfile"):
            keypath = arg
        elif opt in ("-l", "--linkfile"):
            link_path = arg

    if allowlist_path:
        policy = importer.create_ima_policy(allowlist_path, excludelist_path, keypath)
    if link_path:
        policy = intoto_tools.convert_link(link_path, policy)
    print(json.dumps(policy))
    with open("keylime-policy.json", "w") as f:
        f.write(json.dumps(policy))

if __name__ == "__main__":
   main(sys.argv[1:])
