# Mouse 6.0.37: bounded Mac performance diagnostic

This workflow investigates the recorded performance rejection in [publisher 42be, run 45028047196, attempt 1](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45028047196). It does not publish a release or advance an update channel. A successful trace is diagnostic evidence; it is not complete native, source=False, updater or public-release acceptance.

## Recorded problem

The original 20-page comparison rejected a candidate median of 88.836417 ms against the same-job predecessor median 63.293458 ms plus the predeclared 1000/60 ms allowance. The resulting 79.960125 ms limit was exceeded by 8.876292 ms. All five candidate samples were slower than both earlier successful candidate ranges. Existing renderer observations localize an increased selected-to-layout interval, but do not distinguish DOM/layout work, message waits and scheduling.

The original retained scenario and its seven trusted guest clicks passed earlier in that failed job. This does not establish a cause or repair for earlier lost clicks. Source002 and all accepted package bytes remain immutable. Full Mac publication is blocked by the failed original performance gate.

## Scope and ownership

The diagnostic uses the already accepted source `0021084ccb9537e657d21e6f0c8e812dee6b461f` and its exact Mac DMG/ZIP. The existing importer performs reads and local staging with a read-only token. The workflow installs the DMG, checks signatures and arm64, and compares its executable, ASAR and both native addons with the accepted ZIP.

Only the exact `diagnostic/mouse637-mac-performance-trace` branch can execute the native job. Both workflow permissions are read-only: `contents: read` and `actions: read`. The workflow contains no publish, channel, update, owner-marker mutation or full release-acceptance operation. The original release workflows, source/pins and application packages are unchanged.

The installed application runs the original `--mouse-631-smoke` sequence directly: task-only, 20/50-page stress, then stationary media. It uses the original fresh `task-stress-631` profile. It does not replay the preceding full-publisher baseline/retained/owner scenarios. Its timings therefore belong to this separate diagnostic context.

The launcher reuses only the exact hash-bound source002 `run_logged` and `sample_native_exit` definitions; it does not execute the complete verifier script. Original native 350 s, stress 200 s and outer 400 s budgets remain. Inspector setup is asynchronous, bounded to 30 s inside the original outer clock, and the actual Popen/PID is returned immediately.

The owned loopback listener is bound to the spawned PID before resume. Runtime identity is checked before a one-shot loader hook. The exact parent `mouse-631-smoke.cjs` is delegated unchanged and the Inspector server closes before task-only fixture input. At the natural later load of the exact stress module, the original loader is restored before compiling the sole adapted module. On-disk application bytes remain unchanged and signatures are verified before/after.

## Trace interval and limits

Only the 20-page measured loop is traced. Setup and the begin marker occur before the loop; the end marker, stop, stream reads and export occur after it. The original loop bytes, five samples, native operations, assertions, polling and deadlines remain unchanged. No extra input, frame, warmup, await or file write is added inside the measured loop.

The recorder borrows the debugger already attached by the original fixture. It does not detach that connection or take over another target. It owns only its tracing session, listeners, timers, stream and two nonce-qualified UserTiming markers. Cleanup preserves the original failure and records unsuccessful cleanup explicitly.

Bounds:

- 16 MiB primary Chromium event buffer in `recordUntilFull` mode.
- 64 MiB maximum decoded raw export, sequential 256 KiB reads, at most 256 data reads plus one EOF read.
- 10 s setup, 20 s active recording and 15 s stop/drain limits, each also bounded by the remaining original fixture deadline.
- JSON `ReturnAsStream`, no compression; a complete raw JSON document, EOF, known-loss=false, required coverage and an explicit successful `IO.close` are required.

Chromium has a separate 256 KiB metadata buffer. The event-buffer setting is not a bound on total process RAM or browser-side serialization/temp-file usage. The export cap bounds client consumption. Expiry, truncation, missing coverage or cleanup failure makes the diagnostic incomplete; it never becomes valid merely because a success-looking log line exists.

## Protocol and category checks

The observed accepted runtime is Electron 44.5.0 / Chromium 152.0.7977.130 / Node 24.21.0. Each diagnostic records actual `Browser.getVersion`, `process.versions`, `Tracing.getCategories`, the selected config and command lifecycle. Required categories are checked against that actual runtime response:

```text
toplevel
devtools.timeline
blink.user_timing
mojom
mojom.flow
```

There is no wildcard or reduced-category fallback. Source declarations alone do not prove runtime availability. In the pinned implementation, `bufferUsage.eventCount` is 0; positive eventCount is not a validity requirement. A false `dataLossOccurred` reports absence of known loss and must be combined with EOF, framing, markers, PID tracks and complete coverage.

The shell WebContents tracing session covers its filtered target processes plus browser/main and an available GPU. Coverage of all 20 independent guest renderer processes is not asserted. The raw main and shell OS PIDs and their trace tracks must be bound explicitly.

Primary sources:

- [Chromium152 Tracing protocol](https://chromium.googlesource.com/chromium/src/+/152.0.7977.130/third_party/blink/public/devtools_protocol/domains/Tracing.pdl)
- [Chromium152 IO protocol](https://chromium.googlesource.com/chromium/src/+/152.0.7977.130/third_party/blink/public/devtools_protocol/domains/IO.pdl)
- [Chromium152 tracing handler](https://chromium.googlesource.com/chromium/src/+/152.0.7977.130/content/browser/devtools/protocol/tracing_handler.cc)
- [Electron debugger transport](https://www.electronjs.org/docs/latest/api/debugger)

## Reading the result

Raw files are written exclusively into a fresh `mouse637-performance-diagnostic` directory, separate from imported source evidence. The artifact is named `mouse637-macos-performance-diagnostic-attempt-N`. It contains original native reports/logs/PNGs, exact original/adapted module bytes, setup and installed-byte receipts, and the exact assembled trace bytes with hashes. Failed and incomplete runs retain their available raw files.

Use the nonce UserTiming events and actual PID tracks to identify the measured window. Raw trace timestamps are in microseconds on the trace timeline. Node performance.now, renderer performance.now/timeOrigin, Date.now, CDP receipt times and buffered job-log timestamps are separate domains. Only actual matching marker events support a recorded clock mapping; any uncertainty must be retained. IPC attribution requires actual matching flow IDs/scopes and mapped processes, not temporal adjacency.

The original performance threshold remains unchanged. A trace can narrow where work or waiting occurs; it does not by itself prove a product defect, a fix, host contention, or successful release acceptance.

## Local checks

```sh
node --test tools/test_mouse637_performance_trace.cjs
python3 -B -m unittest discover -s tools -p "test_mouse637_performance_trace*.py" -v
```

The workflow checks these before the isolated native diagnostic. Native success, diagnostic integrity and complete release acceptance are separate results.
