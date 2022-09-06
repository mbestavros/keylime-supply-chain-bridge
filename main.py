import getopt, json, sys
from source import importer, intoto_tools

def main(argv):
    owner = None
    repository = None
    token = None
    destination = None
    try:
        opts, _ = getopt.getopt(argv,"ho:r:t:d:",["owner=", "repository=", "token=", "destination="])
    except getopt.GetoptError:
        print('main.py OPTIONS')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("main.py -o <repository owner> -r <repository name> -t <Github access token> -d <artifact destination on Keylime target>")
            sys.exit()
        elif opt in ("-o", "--owner"):
            owner = arg
        elif opt in ("-r", "--repository"):
            repository = arg
        elif opt in ("-t", "--token"):
            token = arg
        elif opt in ("-d", "--destination"):
            destination = arg

    if owner:
        policy = importer.create_ima_policy(owner, repository, token)
    if destination:
        policy = intoto_tools.convert_link(destination, policy)
    print(json.dumps(policy))
    with open("keylime-policy.json", "w") as f:
        f.write(json.dumps(policy))

if __name__ == "__main__":
   main(sys.argv[1:])
