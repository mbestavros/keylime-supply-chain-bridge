# keylime-supply-chain-bridge

A tool to consume software supply chain artifacts (e.g. SBOMs), validate them, and craft them into Keylime policies.

## Usage


### Prerequisites

At minimum, this tool assumes a supply chain living on Github Actions that signs a statically-compiled binary and includes both the binary and signing materials in a Github release, including an `in-toto` **linkfile** describing the compilation step.

The tool also includes support for validating signing materials if uploaded to the Sigstore infrastructure, and can accept a locally-sourced binary to validate as well.

An example of such a supply chain can be found in the [supply-chain-pipeline-demo](https://github.com/mbestavros/supply-chain-pipeline-demo) repository.

In order to interact with Github, a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) is required. Create one and keep it handy.

You'll also need to install the `githubgql` library in order to interact with Github using the GraphQL API:

```shell
> pip install githubgql
```

### Running the tool

```
> python3 main.py <arguments>
```

To view a list of all supported arguments, use `python3 main.py -h`.

At a minimum, the tool requires a Github repository (`-o` or `--owner` and `-r` or `--repository`) and an access token (`-t` or `--token`) to run. Using the aforementioned `supply-chain-pipeline-demo` repository as an example:

```shell
> python3 main.py -o mbestavros -r supply-chain-pipeline-demo -t <your access token>
```

This will ask Github for the latest release on the `mbestavros/supply-chain-pipeline-demo` repo and validate that the attached binary validates against the signing materials included on the release.

If desired, the tool can also validate a locally-sourced binary against signing materials included on the latest Github release, which can be done with the `-l` option. For example, to validate a local binary at path `/root/hello-go`:

```shell
> python3 main.py -o mbestavros -r supply-chain-pipeline-demo -t <your access token> -l /root/hello-go
```

### Writing to a Keylime policy

The tool can also forward validated hashes to a Keylime policy.

Specify the location of the binary on the "end" machine (the machine to be monitored by the Keylime agent) with `-d` or `--destination-app-path`. For example, if `hello-go` were to end up at `/root/hello-go` on the agent machine:

```shell
python3 main.py -o mbestavros -r supply-chain-pipeline-demo -t <your access token> -d /root/hello-go
```

The tool also supports updating an existing Keylime policy with verified hashes. Specify the file path of an existing allowlist with `-a` or `--allowlist`. For example, with an existing allowlist at `/root/allowlist.txt`:

```shell
python3 main.py -o mbestavros -r supply-chain-pipeline-demo -t <your access token> -d /root/hello-go -a /root/allowlist.txt
```

Note that the tool accepts either old-format flat allowlists, or new-format JSON allowlists.

The tool will write a file called `keylime-policy.json` in the current directory, which can be used directly with Keylime.

### Validating against Sigstore

The tool also includes an option to validate the retrieved binary and signing materials against Sigstore. Use `-s` or `--sigstore` to:

- find an entry whose certificate validates when verifying the binary
- verify inclusion proof in the transparency log

as an additional check on top of the existing checks.
