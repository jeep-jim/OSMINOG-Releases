# Release-feed signing

The feed envelope contains `signed` and `signature`.

The Ed25519 signature covers canonical UTF-8 JSON of the `signed` object with recursively sorted keys and no insignificant whitespace.

Active key ID: `osminog-release-2026-01`.

The private key is never committed. It must be stored as a protected secret in the private source repository before automatic signing is enabled.

Until then, the publication workflow leaves `signature: null`; Dev Hub 2.0 must treat such a feed as an explicit internal bootstrap state and must never present it as production-signed.
