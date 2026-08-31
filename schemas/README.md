# Schemas

`osminog-update-feed-envelope-v1.schema.json` defines the signed channel-feed envelope.

The Ed25519 signature is calculated over canonical UTF-8 JSON of the `signed` object with recursively sorted keys and no insignificant whitespace.

`osminog-release-manifest-v1.schema.json` defines immutable release metadata.
