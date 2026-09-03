# OSMINOG Chrome 3.16.0 — SIMPLE ACCESS RUNTIME

OSMINOG returns to a simple capability model.

- normal canvas, file, app, module, browser, graphics and project work is always available to the connected AI; there is no Poseidon or AI-edit permission toggle;
- **Access** contains only canvas sharing: visibility, share link and view/comment/edit role;
- the connector is automatic, but normal chat prompts do not preload the canvas/project; context is requested only when the user explicitly mentions the canvas/project/desktop/selection, attaches an object or uses a tether;
- the same lazy-context policy applies to built-in Google AI and external ChatGPT Presence;
- changing the private OSMINOG product source is a just-in-time privileged action, not a user setting;
- first Owner Unlock verifies the local GitHub credential against `jeep-jim/OSMINOG` and `jeep-jim/OSMINOG-Releases`, then enrolls a Google Authenticator-compatible TOTP secret; future source actions require the six-digit code and unlock for 15 minutes;
- GitHub credentials and TOTP codes are never inserted into AI chat text.

Security boundary: this release uses standard TOTP compatible with Google Authenticator. True push approval requires an external identity/backend service and is not claimed here.

Package SHA-256: `840adfc1f8cbfbf04b0727e3b447d0724c4581133e2d7d71632665a1f77ee0bd`
Package bytes: `578416`
Source commit: `1f6bee0f4b8cc1de6a6d62d6dc39ec7ee657732a`
