# Mouse Browser 6.0.42

## Navigation and saved grid

- Links within the same site keep the current tab and WebContents. Links to another site open a new tab. Same host and parent/child subdomains remain one site across ports and schemes.
- In classic view, the corner minimize control restores the saved grid without closing tabs or discarding the workspace. In grid view it retains native window minimization.

## Appearance and input language

- A thermometer button in the bottom panel opens white and black tone controls. Presets and sliders adjust brightness/depth and warm/cool temperature; the same controls are available in Settings → Appearance. Normal-mode choices survive restart, while private-mode adjustments stay within that private session.
- Interface language is selected only in Settings, with more space around the dropdown arrow.
- The footer language indicator shows the actual system input layout. One tap switches to the chosen or previous alternate layout; its arrow lists installed layouts.
- Local Russian ↔ English layout detection can offer to convert text typed with the wrong keyboard layout. Only explicit OK changes the original field. The offer can be declined and becomes invalid when the text or target changes. Supported plain-text and paragraph editors keep their surrounding content and native Undo; passwords and IME composition are excluded.

On Linux, reading and switching the system input layout currently requires X11. Wayland sessions report this control as unavailable instead of displaying an invented layout.

Profile, App ID, Chromium partition, cookies, tabs, desktops, installed updates and the existing feature suite remain required. The actual published predecessor is 6.0.41; legacy 6.0.29 update compatibility remains checked where supported.

macOS Apple Silicon remains an ad-hoc-signed preview without Developer ID notarization. Windows remains an unsigned preview. Linux packages are AppImage and deb; CI on Ubuntu does not claim testing on the owner’s Linux Mint device.
