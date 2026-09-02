# OSMINOG Chrome 3.12.4 — DOCK PERFORMANCE HOTFIX

This hotfix removes two render loops introduced in 3.12.3 and moves application launchers out of the zoomable canvas.

- The window manager no longer observes and rewrites its own `style` attribute.
- Window visibility monitoring is limited to the `hidden` attribute, without continuous render polling.
- The Module Store empty-result state cannot schedule an unbounded repaint loop.
- Extension, provider and self-created module icons live in one fixed bottom dock outside `#world`.
- All application icons use one size and the same visual/hover behavior as Nano Banana.
- A single click opens or restores an application; restored and new windows come to the front.
- Closing or minimizing reusable windows returns them to the dock.
- Legacy canvas launchers are removed automatically; canvas zoom no longer changes application icon size.

Package: OSMINOG-Chrome-3.12.4-DOCK-PERFORMANCE-HOTFIX.zip

Size: 439183 bytes

SHA-256: 1dd90680a22ad27f481b42225379cdd6b0d2f6ee172874915d97d37c991512f5

Source commit: [ef21ab0](https://github.com/jeep-jim/OSMINOG/commit/ef21ab0441eb3d6d7da98eaaba23bccd0970e6b8)
