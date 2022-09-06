import copy, datetime, json, re
from os.path import exists
from .constants import constants
from . import signing


# Creates an IMA policy from provided legacy allow and exclude lists.
def create_ima_policy(allowlist_path, excludelist_path, keypath):
    with open(allowlist_path, "r") as f:
        alist_raw = f.read()

    p = re.compile(r"^\s*{")
    if p.match(alist_raw):
        alist_json = json.loads(alist_raw)

        # verify it's the current version
        if "meta" in alist_json and "version" in alist_json["meta"]:
            version = alist_json["meta"]["version"]
            if int(version) <= constants.ALLOWLIST_CURRENT_VERSION:
                print("Allowlist has compatible version %s", version)
            else:
                # in the future we will support multiple versions and convert between them,
                # but for now there is only one
                raise Exception("Allowlist has unsupported version {version}")
        else:
            print("Allowlist does not specify a version. Assuming current version %s", constants.ALLOWLIST_CURRENT_VERSION)
    else:
        alist_json = convert_legacy_allowlist(alist_raw)

    excl_list = []
    with open(excludelist_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            excl_list.append(line)

    ima_policy = copy.deepcopy(constants.EMPTY_IMA_POLICY)

    ima_policy["digests"] = alist_json["hashes"]
    ima_policy["excludes"] = excl_list
    ima_policy["keyrings"] = alist_json["keyrings"]
    ima_policy["ima"] = alist_json["ima"]

    if keypath:
        attached_sig = signing.sign(ima_policy, keypath)

        ima_policy_signed = copy.deepcopy(constants.EMPTY_SIGNED_IMA_POLICY)
        ima_policy_signed["signatures"].append(attached_sig)
        ima_policy_signed["signed"] = ima_policy
        ima_policy = ima_policy_signed

    return ima_policy


# Converts flat-format allowlist to newer JSON-format allowlist
def convert_legacy_allowlist(alist_raw):
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
    return alist
