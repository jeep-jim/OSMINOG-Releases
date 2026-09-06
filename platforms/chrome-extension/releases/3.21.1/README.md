# OSMINOG 3.21.1 — media reference and chat performance

- Mixed search/generate requests offer “Найти в интернете” and “Сгенерировать” buttons in the local chat. Explicit generation does not require that choice.
- Composer attachments reach the active sending path. Generation with a selected image captures that reference, including “same person, different pose” requests.
- Returned HTTPS image files can be imported through asset_create. Generated files are positioned to the right of the original reference.
- Successful image imports do not trigger another vector-patch request. Missing generated files produce an explicit failure rather than a primitive substitute.
- Search downloads the original before falling back to a thumbnail and bounds stalled requests.
- Chat initially renders 80 recent messages and can show older messages. Complete local history is retained. Outgoing history is bounded to 24000 characters; chat_history_read retrieves older messages from the current project's threads.

Validation: source/behavioral and browser CI. Actual provider image generation and latency on the user's machine remain unverified. This change repairs image routing and delivery; it does not provide a new image generation backend or restore external conversation mirroring. Browser permission is requested from the send/choice action when image downloads require it.

All three CI workflows passed at a61679c583bb1541ecc0254e4b5d102fa4438297. Browser: choice controls, long-history expansion, graphics, documents and HTML export. Failure-path progress timer cleanup included.
