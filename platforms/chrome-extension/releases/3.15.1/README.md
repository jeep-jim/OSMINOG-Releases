# OSMINOG Chrome 3.15.1 — OWNER ACCESS RECOVERY

- fixes Owner/Poseidon lockout caused by temporary GitHub status failures;
- keeps a previously verified owner grant for up to 30 days while the local GitHub token remains present;
- adds fine-grained GitHub token setup directly to Control Center; secrets are never inserted into AI chat text;
- GitHub and other protected sites use managed real Chrome tabs instead of blocked iframes, inheriting the same Chrome profile, system VPN/proxy and installed browser extensions;
- active managed tabs are restored and focused correctly;
- normal users keep Interactive Workspace capabilities but cannot unlock OSMINOG product source/release tools without verified write access to the private owner repository.

Recommended token repositories: `jeep-jim/OSMINOG` and `jeep-jim/OSMINOG-Releases`. Permissions: Contents Read/Write, Pull requests Read/Write, Actions Read/Write.

Package SHA-256: `aa639f889a46b580dd1a0ec4777cf046a2cb04fd4e925682eed7de0af77fca5f`
Package bytes: `582018`
Source commit: `a06311405d7669102abd8e24af64fd539e421143`
