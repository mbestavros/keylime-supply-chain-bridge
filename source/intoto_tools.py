import copy, datetime, requests, shutil, sys, tempfile
from in_toto import verifylib
from in_toto.models.layout import Layout, Step, Inspection
from in_toto.models.metadata import Metablock
from securesystemslib.interface import (generate_and_write_rsa_keypair,
    import_rsa_privatekey_from_file, import_ed25519_publickey_from_file)
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

def verify_layout(artifacts, link_urls, id_key_urls, intoto_args):
    # Dictionary to store all functionary keys
    functionary_keys = {}

    # Since in-toto validates files in a directory, use a temporary directory for verification.
    with tempfile.TemporaryDirectory() as tmpdirname:

        # Write artifacts to verification directory
        for artifact_name in artifacts.keys():
            with open(f"{tmpdirname}/{artifact_name}", "wb") as f:
                f.write(artifacts[artifact_name])

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

        if intoto_args.get("layout_path") and intoto_args.get("layout_key"):
            metablock = Metablock.load(intoto_args["layout_path"])
            layout_key = import_rsa_privatekey_from_file(intoto_args["layout_key"], password=intoto_args.get("layout_key_password"))

        elif bool(intoto_args.get("layout_path")) ^ bool(intoto_args.get("layout_key")):
            print("ERROR: Both --intoto and --intoto-key are required for custom layout checks!")
            sys.exit(1)
        else:
            # Create a layout key
            layout_key_path = generate_and_write_rsa_keypair(password="123", filepath=f"{tmpdirname}/layout_key")
            layout_key = import_rsa_privatekey_from_file(layout_key_path, password="123")

            layout = Layout()

            # Add functionary keys from Github to layout
            for key_name in id_key_urls.keys():
                imported_key = import_ed25519_publickey_from_file(f"{tmpdirname}/{id_key_urls[key_name]['filename']}")
                functionary_keys[key_name] = layout.add_functionary_key(imported_key)

            layout.set_relative_expiration(days=1)

            step_compile_name = "compile"
            step_compile = Step(name=step_compile_name)
            step_compile.pubkeys = [functionary_keys["developer"]["keyid"]]

            step_compile.set_expected_command_from_string("go build")

            step_compile.add_product_rule_from_string("CREATE hello-go")
            step_compile.add_product_rule_from_string("DISALLOW *")

            inspection = Inspection(name="inspect")
            inspection.set_run_from_string("echo hello")
            materials_list = ",".join(artifacts.keys())
            inspection.add_material_rule_from_string(
                f"MATCH {materials_list} WITH PRODUCTS FROM {step_compile_name}")

            layout.steps = [step_compile]
            layout.inspect = [inspection]

            metablock = Metablock(signed=layout)
            metablock.sign(layout_key)
            metablock.dump(f"{tmpdirname}/root.layout")

        key_dict = {layout_key["keyid"]: layout_key}
        verifylib.in_toto_verify(metablock, key_dict, tmpdirname)
