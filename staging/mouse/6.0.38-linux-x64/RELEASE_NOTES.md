# Mouse Browser 6.0.38 — Linux x64

This release improves new-tab painting and pane edges. Rectangular grids use one-pixel separators; rounded grids retain their spacing and corners. The white-tone setting also applies to neutral light text on dark web pages while preserving colored content and light surfaces.

## Installation

For Ubuntu and Linux Mint, use **Mouse-Browser-6.0.38-Linux-x64.deb**. From its download directory:

```sh
sudo apt install ./Mouse-Browser-6.0.38-Linux-x64.deb
```

The package declares the required GBM and audio libraries, including the Ubuntu 24.04 audio-library alternative. Clean installation and restart on Ubuntu 24.04 are required release checks. An AppImage is also provided. Existing browser profiles, tabs, workspaces and update paths are retained.

## Install a store extension

Open the extension's page in Chrome Web Store, open Mouse's Extensions menu and choose **Install in Mouse**. Review the requested access in Mouse's native confirmation. The browser checks the store package and its signatures before installation. The manager supports enable/disable, pinning and removal; supported extension APIs remain limited by Electron.
