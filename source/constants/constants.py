# hardcoded constants - should eventually be referenced from Keylime
ALLOWLIST_CURRENT_VERSION = 5
EMPTY_ALLOWLIST = {
    "meta": {
        "version": ALLOWLIST_CURRENT_VERSION,
    },
    "release": 0,
    "hashes": {},
    "keyrings": {},
    "ima": {"ignored_keyrings": [], "log_hash_alg": "sha1"},
}

IMA_POLICY_CURRENT_VERSION = 1
EMPTY_IMA_POLICY = {
    "meta": {
        "version": IMA_POLICY_CURRENT_VERSION
    },
    "release": 0,
    "digests": {},
    "excludes": [],
    "keyrings": {},
    "ima": {
        "ignored_keyrings": [],
        "log_hash_alg": "sha1"
    },
    "ima-buf": {},
    "verification-keys": [],
}

EMPTY_SIGNED_IMA_POLICY = {
    "signatures": [],
    "signed": {}
}
