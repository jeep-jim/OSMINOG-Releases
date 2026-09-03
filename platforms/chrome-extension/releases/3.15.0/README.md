# OSMINOG Chrome 3.15.0 — INTERACTIVE CAPABILITY RUNTIME

Product-runtime expansion after owner live testing of 3.14.5.

- stopwatch, calendar and music-player requests use host-owned deterministic widget creation, so the connected AI cannot lose `module_create` after one successful app;
- every provider request receives a fresh capability lease; generic apps use one contract: AI creates the UI/code, OSMINOG installs and verifies it;
- the music-player widget can read a selected canvas audio asset through sandbox permission `assets.read`;
- audio/video files play in the built-in workbench; spreadsheet, ROM and APK binaries are preserved as File Lab assets available to AI-built applications;
- Graphics Studio exposes native editable `graphics_create` layers using the canvas vector/shape/text/image model, including Bézier paths, masks, gradients, opacity and stroke;
- Poseidon/source/release capabilities are gated to verified write access to the private owner repository; normal users keep the interactive workspace without product-source authority.

Boundary: Chrome does not execute Android APK files natively. Console ROM execution also requires a compatible emulator core; 3.15.0 provides the binary asset-to-sandbox-app foundation rather than pretending arbitrary binaries are executable.

Package SHA-256: `9838c05ded643e4034cc9ce601e64819b94e94f98878a83f8a48f03283e20031`
Package bytes: `580151`
Source commit: `8e9e2278d8064df97bf5b795689d6b10fd3a2a89`
