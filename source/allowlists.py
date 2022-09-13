import copy, datetime, json, re
from .constants import constants

# Looks for allowlists at allowlist_path, converts it to new JSON format if necessary, then returns.
def get_allowlist(allowlist_path=None):
    if allowlist_path:
        with open(allowlist_path, "r") as f:
            alist_raw = f.read()

        p = re.compile(r"^\s*{")
        if p.match(alist_raw):
            alist = json.loads(alist_raw)
        else:
            alist = copy.deepcopy(constants.EMPTY_ALLOWLIST)
            alist["meta"]["timestamp"] = str(datetime.datetime.now())
            alist["meta"]["generator"] = "keylime-legacy-format-upgrade"

            for line in alist_raw.splitlines():
                line = line.strip()
                if len(line) == 0:
                    continue

                pieces = line.split(None, 1)
                if not len(pieces) == 2:
                    print("Line in Allowlist does not consist of hash and file path: %s", line)
                    continue

                (checksum_hash, path) = pieces

                if path.startswith("%keyring:"):
                    entrytype = "keyrings"
                    path = path[len("%keyring:") :]  # remove leading '%keyring:' from path to get keyring name
                else:
                    entrytype = "hashes"

                if path in alist[entrytype]:
                    alist[entrytype][path].append(checksum_hash)
                else:
                    alist[entrytype][path] = [checksum_hash]
    else:
        alist = copy.deepcopy(constants.EMPTY_ALLOWLIST)
        alist["meta"]["timestamp"] = str(datetime.datetime.now())
        alist["meta"]["generator"] = "keylime-policy-importer"
    return alist

# Reads an in-toto .link file present at link_path and converts it to a Keylime
# policy, or appends to an existing policy if provided.
def append_path_to_allowlist(alist, path, hash):
    entrytype = "hashes"
    if path in alist[entrytype]:
        alist[entrytype][path].append(hash)
    else:
        alist[entrytype][path] = [hash]
    return alist
