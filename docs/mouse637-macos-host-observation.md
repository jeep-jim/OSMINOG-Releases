# Mouse 6.0.37: external Mac process observation

## Reason for this experiment

The full [42be publisher run 45028047196, attempt 1](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45028047196) passed the retained native interaction scenario, then stopped at the existing desktop performance comparison. The 20-page median was 88.836417 ms; the unchanged predecessor-plus-one-frame limit was 79.960125 ms. Publication and channel updates were skipped. The failure remains part of the release record.

The subsequent [isolated c3be diagnostic, run 45033443992, attempt 1](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45033443992), collected a bounded Chromium trace from the same accepted package. It was not a publication run and its timings cannot replace the original comparison. Artifact 14758059097 is 5,789,846 bytes, SHA256 `a4a69ee8eb78bc74994ac712e563b26c8cd5736963a999a9d7b6ba4df5220d45`.

The trace and exact source review did not establish a missing capture await. All twelve tasks posted from `MaybeNotifyReady` were outside all five renderer live-switch intervals even after accounting for clock conversion and timestamp precision; the smallest conservative separation was 6.437 ms. The task's posting location is not its exclusive C++ execution time. Invoke messages identify an Electron IPC method, but do not disclose the application channel. These observations do not establish the cause of the earlier 42be failure.

The next experiment records external host and process accounting during one complete original publisher run. It adds information about process CPU consumption, cumulative runnable accounting and host CPU activity without tracing the performance workload through CDP. It does not change the comparison, select a favorable subset of samples or add a settling delay.

## Scope and phase boundaries

| Phase | Original launch observed | Original outer budget |
| --- | --- | --- |
| Baseline | The existing Python `mouse-637-baseline-performance.py --output` invocation and its owned descendants | 900 seconds |
| Candidate | The installed `Mouse Browser --mouse-631-smoke` invocation and its owned descendants | 400 seconds |

The outer Python adapter delegates the existing guest-input observer and feature-readiness driver unchanged. It returns the actual original `Popen` object immediately. Arguments, environment, logs, native process identity, phase order, profiles, inputs, deadlines and assertions remain those of the original verifier. Observation is prepared asynchronously after each of the two actual launches. No product file or performance module is transformed, no inspector is attached to these phases, and no retry is performed.

The compiled helper observes only its designated process tree. Records bind PID, parent, UID, executable path and creation identity; a PID is not an enduring identity by itself. Already observed identities that become reparented remain explicit in the record. Unrelated processes, new orphans and a reused PID are not silently adopted. Host counters describe aggregate CPU activity without collecting other processes' arguments or environment.

Python framework executables need an explicit image policy. In CPython 3.12.10, the [framework launcher at the exact release commit](https://github.com/python/cpython/blob/0cc81280367df838c4b199f8f0378837165071c2/Mac/Tools/pythonw.c) invokes the interpreter inside `Resources/Python.app` using `POSIX_SPAWN_SETEXEC`. A process can therefore retain its creation identity while changing executable image during startup. That source permits this runtime pattern; it does not identify a destination missing from an earlier raw observation.

Only the baseline Python phase and the synthetic fixture permit the known parent-runtime handoff. The helper records the already running parent Python process's PID, UID, BSD and Mach creation identity, executable path/UUID and read bounds. The root must retain the original PID, UID, parent and birth within its original launch bracket. Its initial image must match the original launch path or the exact observed parent runtime. When starting in the launcher image, at most one forward transition to that same runtime is accepted, with the parent identity and image checked again. Starting in the runtime grants no later transition. Candidate Mouse keeps a fixed root image; arbitrary, reverse or third-image transitions fail and their observed image tuple is retained. These witnesses let the independent reader check the same state changes. The launch, deadline and sampling clocks are never reset for this handoff.

The target sample interval is 250 ms, not a claim of exact scheduling. The helper has explicit elapsed-time, identity, record and output bounds. Collection is limited to 256 owned identities, 65,536 records and 64 MiB per phase. Read intervals, scheduling lag, errors, limits and termination are retained. A cap, missing required API, denied read or incomplete stream cannot be presented as a complete measurement. Only the observer is stopped during observer cleanup; it does not kill or change the priority of the measured browser.

## What the counters mean

The helper uses the system Mac headers and reads `proc_pid_rusage(RUSAGE_INFO_V4)`, process identity information and host CPU ticks. Raw Mach values are accompanied by the actual timebase. The reader keeps these clocks separate from renderer and main `performance.now`.

`ri_runnable_time` is process-wide accounting accumulated over threads, including running and runnable time. It is not a direct measurement of a main-thread queue delay. Active runnable timer accounting and CPU accounting are sampled differently; subtracting them does not produce an exact scheduler-wait duration. Host CPU tick differences also do not identify which process caused a delay. The helper records its own CPU use and sampling cost; negligible overhead is not assumed in advance.

Before native execution, the observation-quality budget is fixed at sampler user-plus-system CPU time no greater than 1% of one logical CPU over the actual observed lifetime of each phase. It is not divided by the number of host cores. The independent reader recomputes the ratio from the raw values. This limits measured aggregate CPU consumption; it does not prove zero interference, bound an individual switch's delay or account for every indirect effect of collection. Per-sample accounting and read/scheduling delays remain available even when the aggregate budget passes. No original browser-performance threshold is changed by this additional condition.

The API interpretation is checked against Apple's published XNU sources, including `bsd/kern/bsd_kern.c`, `bsd/kern/proc_info.c`, `osfmk/kern/task.c`, `osfmk/kern/sched_prim.c` and `osfmk/kern/timer.h` at `xnu-11417.140.69`. Actual API availability and permissions are checked on the Mac runner before publication execution. These source checks are not a claim that every kernel implementation detail has been independently verified on the running host.

## Verification and release decision

The PR contract compiles the helper on `macos-15` and exercises it on an owned test process tree without launching Mouse. Portable tests cover observer ownership, original-launch preservation, bounds and failure handling. The independent reader validates raw stream completeness, phase/process binding, original native receipts and the exact tool and helper bytes.

The pure raw-stream parser can also check the separate synthetic fixture under its existing 500–10,000 ms budget. The complete publication reader still requires exactly the original baseline and candidate phases, with their fixed 900- and 400-second budgets; fixture data cannot replace either phase.

The build receipt records the actual Git checkout, committed source and builder bytes, compiler/SDK queries, compilation arguments and results, binary checksum and `lipo` architecture. The executed helper binary and the two original consumed Python verifier files are included in the verification artifact. This permits direct byte checks; it does not assert a hermetic or reproducible compiler environment.

The original feature-readiness and guest-input readers remain separate mandatory checks. The new reader is additive and does not replace the installed native acceptance, immutable package verification, performance comparison, public package download or shipped-updater checks. If the original verifier fails, its original error takes precedence and partial observations remain available. If it succeeds, both observation streams must be complete before the normal publication path proceeds.

Source `0021084ccb9537e657d21e6f0c8e812dee6b461f`, accepted DMG/ZIP bytes, signatures, pins, all original performance criteria and the existing public Windows/Linux 6.0.37 packages are unchanged. No claim of a performance repair or physical owner-Mac verification is made by this instrumentation. A successful original full publisher run may establish release acceptance without establishing the cause of a previous intermittent failure; a failed run must remain failed and supply its actual observations for the next decision.

## Preserved PR preflight outcomes

The initial [c221 run 45038399839, attempt 1](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45038399839) failed before compilation because a builder helper's positional `path` parameter collided with the receipt's `path=` metadata. The scoped correction renames that parameter and adds regressions covering the actual build function with real temporary Git checks and explicitly synthetic compiler responses. The original failing bytes and corrected passing tests are retained.

The corrected [c3d run 45039163231, attempt 1](https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/45039163231) passed 168 Python and 26 JavaScript contract tests and compiled the arm64 helper with Apple clang 17.0.0 against SDK 15.5. Its actual owned-process fixture failed: the sampler recorded `root-image-changed` for the original same-birth root and exited 1. The subsequent child wait timed out and fixture cleanup killed its own test child. The rejected destination path and UUID were not retained in that version, so the exact image transition in this failed attempt is not claimed.

Artifact 14760399449 is 13,984 bytes, SHA256 `faf9386edf60bff0f32475520c4c86c0624dc7ac9c4ef3cca288f645823d3a9c`. Its five files preserve the actual binary, successful build receipt, exact test child, failed native receipt and partial raw stream. The short 317.199 ms stream also exceeded the independent 1% self-CPU limit; neither failure is waived. No Mouse product or full publisher ran in either PR preflight. The reviewed runtime-handoff correction requires its own actual Mac contract before merge and full publication execution.
