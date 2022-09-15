import copy, datetime, requests, os, tempfile
from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock
from securesystemslib.interface import (generate_and_write_rsa_keypair,
    import_rsa_privatekey_from_file)
from .constants import constants

# Reads an in-toto .link file present at link_path and converts it to a Keylime
# policy, or appends to an existing policy if provided.
def convert_link(link_path, policy=None):
    if not policy:
        policy = copy.deepcopy(constants.EMPTY_ALLOWLIST)
        policy["meta"]["timestamp"] = str(datetime.datetime.now())
        policy["meta"]["generator"] = "keylime-policy-importer"

    link = Metablock.load(link_path)
    artifacts = link.signed.products

    for path in artifacts.keys():
        entrytype = "digests"
        hash = artifacts[path]["sha256"]
        if path in policy[entrytype]:
            policy[entrytype][path].append(hash)
        else:
            policy[entrytype][path] = [hash]

    return policy

def verify_layout(artifact, link_urls, id_key_urls):
    # Dictionary to store all functionary keys
    functionary_keys = {}

    # Since in-toto validates files in a directory, use a temporary directory for verification.
    with tempfile.TemporaryDirectory() as tmpdirname:

        # Write artifact to verification directory
        with open(f"{tmpdirname}/artifact", "wb") as f:
            f.write(artifact)

        # Write linkfiles from Github to verification directory
        for link in link_urls.keys():
            link_response = requests.get(link_urls[link]["url"])
            with open(f"{tmpdirname}/{link_urls[link]['filename']}", "wb") as f:
                f.write(link_response.content)

        # Write keyfiles from Github to verification directory
        for key_name in id_key_urls.keys():
            key_response = requests.get(id_key_urls[key_name]["url"])
            with open(f"{tmpdirname}/{id_key_urls[key_name]['filename']}", "wb") as f:
                f.write(key_response.content)

        # Create a layout key
        layout_key_path = generate_and_write_rsa_keypair(password="123", filepath=f"{tmpdirname}/layout_key")
        layout_key = import_rsa_privatekey_from_file(layout_key_path, password="123")

        layout = Layout()

        # Add functionary keys from Github to layout
        for key_name in id_key_urls.keys():
            functionary_keys[key_name] = layout.add_functionary_key_from_path(f"{tmpdirname}/{id_key_urls[key_name]['filename']}")

        layout.set_relative_expiration(days=1)

        step_compile = Step(name="compile")
        step_compile.pubkeys = [functionary_keys["developer"]["keyid"]]

        step_compile.set_expected_command_from_string("go build")

        step_compile.add_product_rule_from_string("CREATE /home/runner/work/supply-chain-pipeline-demo/supply-chain-pipeline-demo/hello-go/hello-go")
        step_compile.add_product_rule_from_string("DISALLOW *")

        inspection = Inspection(name="inspect")
        inspection.add_material_rule_from_string(
            "MATCH artifact WITH PRODUCTS FROM compile")

        layout.steps = [step_compile]
        layout.inspect = [inspection]

        metablock = Metablock(signed=layout)
        metablock.sign(layout_key)
        metablock.dump(f"{tmpdirname}/root.layout")

        print(os.listdir(tmpdirname))
