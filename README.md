# OSMINOG Releases

Public, release-only distribution registry for OSMINOG.

This repository contains **verified packaged builds, update feeds, schemas, public verification keys and release metadata** for every OSMINOG platform. Product source code remains private in `jeep-jim/OSMINOG`.

## Platforms

1. Web + PWA
2. Chrome extension
3. Windows desktop
4. macOS desktop
5. Android
6. iOS

## Channels

- `dev` — rapid internal development builds
- `beta` — wider pre-release validation
- `stable` — production-approved builds

## Update rules

- Every published build is immutable and versioned.
- Full packages are the recovery source of truth; differential patches are optional only.
- A channel feed may advance only after the remote package exists and its size and SHA-256 are verified.
- Packages must preserve platform identity requirements, including the fixed Chrome extension key where applicable.
- Failed or incomplete publications must never be announced as available updates.

## Distribution model

- Chrome development: OSMINOG Dev Hub managed folder + Native Messaging.
- Chrome production: Chrome Web Store.
- Windows/macOS desktop: signed native updater.
- Android/iOS production: platform stores.
- Web/PWA: atomic deployment and service-worker versioning.

See `registry.json`, `channels/`, `schemas/`, `platforms/`, `devhub/` and `public-keys/`.
