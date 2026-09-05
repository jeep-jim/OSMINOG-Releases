# OSMINOG Chrome 3.20.0 — AI Workspace Core Merge

- proven 3.11.26 chat execution contracts are retained in the current runtime;
- agent threads and drag-to-object links remain active;
- canvas mutations use validated `briefcraft.patch/v1` actions;
- a prose-only response to an edit command triggers a patch retry;
- native file and image drop is guarded against duplicate execution;
- Shared Vision keeps structured context and the attached image on one project revision;
- tool execution is bounded and reports failures without locking the interface.

Runtime owner verification is required after updating from 3.19.12.
