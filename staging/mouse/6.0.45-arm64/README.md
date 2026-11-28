# Mac 6.0.45 staging — unready

`pin.json` deliberately has `ready: false`, null candidate provenance and null current package hashes. No `PUBLISH_OWNER` is present. The publisher cannot import, publish or advance the update channel from this template.

## Activation requirements

1. Pin the exact merged source commit, successful Mac workflow attempt and job, candidate/verification artifact IDs and ZIP SHA256 values, and both package byte sizes and SHA256 values. The current predecessor stays the immutable accepted 6.0.44 Mac package; 6.0.29 coverage is retained independently.
2. Preserve all retained raw-evidence validators. Source and fresh installed runs must independently pass both new645 gates: native account/Flash sidebar and OS pixels; real HTTP/SQLite identity, two logical device profiles, fourteen installed processes, metadata-only sync, fresh guest isolation and missing-credential startup protection. Separately pin `rtc.run`, `rtc.attempt`, `rtc.job`, `rtc.artifact` and `rtc.archiveSHA256` for the successful `direct-transfer` job in `mouse-flash.yml` on that same source commit. Its immutable raw JSON, log and screenshots must prove real non-relayed RTC, consent before data, interruption/resume and continued payload after broker/STUN shutdown. This is source acceptance on one CI Mac, not a physical two-Mac or terabyte test.
3. Keep the reviewed helper graph under `tools/mouse645-source/` consistent with the exact accepted source. Account fixture imports require `tools/`, `desktop/` and `services/` in their original relationship. The importer checks Git blob IDs and the separately reviewed SHA256 manifest before executing any new helper. Old flat helper copies remain for the retained validators; the native driver runs as `mouse645-release/tools/mouse-verify.py`.
4. Own-server public HTTPS and UDP STUN must be operational. Publication and channel advancement each invoke the pinned read-only `infra/mouse-services/public-probe.py` afresh. The HTTPS identity issuer must match the key in the shipped client, the broker must answer its own route and UDP3478 must return a valid binding. A saved success receipt is insufficient. The probe creates no accounts, rooms or uploaded files.
5. Only after these prerequisites and release authorization are satisfied may `ready` become true and the exact owner trigger be added. The current template makes neither claim.

## Preparation checks

```sh
python3 -m unittest discover -s tools -p 'test_mouse645_*.py' -v
python3 -m py_compile tools/mouse645-*.py
python3 tools/mouse645-release.py validate-template
python3 tools/mouse645-publish-plan.py macos-arm64
```

The final command must currently print `publish=false`. No645 Windows/Linux stages or channel mutations are authorized by this Mac-only workflow. Frozen642 publishers and all earlier release files remain unchanged.
