import copy, datetime
from in_toto.models import metadata
from .constants import constants

# Reads an in-toto .link file present at link_path and converts it to a Keylime
# policy, or appends to an existing policy if provided.
def convert_link(link_path, policy=None):
    if not policy:
        policy = copy.deepcopy(constants.EMPTY_ALLOWLIST)
        policy["meta"]["timestamp"] = str(datetime.datetime.now())
        policy["meta"]["generator"] = "keylime-policy-importer"

    link = metadata.Metablock.load(link_path)
    artifacts = link.signed.products

    for path in artifacts.keys():
        entrytype = "digests"
        hash = artifacts[path]["sha256"]
        if path in policy[entrytype]:
            policy[entrytype][path].append(hash)
        else:
            policy[entrytype][path] = [hash]

    return policy
