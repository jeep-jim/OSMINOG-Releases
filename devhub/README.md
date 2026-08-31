# OSMINOG Dev Hub

Native updater packages and metadata live here.

Dev Hub owns the managed Chrome development root:

`%LOCALAPPDATA%\OSMINOG\Chrome\current`

Dev Hub must verify the signed feed, package size, SHA-256, root manifest version and fixed extension identity before replacing the live build. It stages, backs up, applies atomically and rolls back when the new build fails to boot.
