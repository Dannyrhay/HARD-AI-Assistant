# Verification record

Date: 13 September 2026

## Passed

- 34 isolated automated tests; no real email sent.
- JavaScript syntax validation and Python compilation.
- Browser: actual DOCX upload, document approval, actual Word-to-PDF conversion, PDF approval, persistence across reload/service restart.
- Actual Word export produced a readable one-page PDF. Rendered with Poppler and visually inspected: title, paragraphs and fee lines were intact without overlap or clipping.
- Browser: Settings accurately shows Gmail/Outlook unconfigured and prevents connection actions until OAuth application setup exists.
- Browser: 200% text at a 390px viewport did not cause horizontal overflow in Settings; home also checked.
- Unit tests cover original preservation, duplicate import, malformed files, tracked changes, scanned-PDF blocking, folder boundaries, verified contact matching, typo suggestions, immutable EML attachments, changed attachment/sender rejection, single-use send approval, uncertain-send state, OAuth PKCE/state replay, DPAPI token encryption and HTTP Host/Origin/CSRF/static-data protections.

## Not verified / release blockers

- Live Gmail/Outlook OAuth, refresh, revoke, send, receive, bounced-message detection and Outlook MIME opening. Account application credentials and authorised test accounts required.
- Word layout fidelity beyond the one-page fictional fixture; locked files, long documents, images, annexes, font substitution, activation and timeout cleanup on the target machine.
- Actual microphone capture and audible screen reading; browser APIs are optional with visible fallback messages.
- AI review, OCR, cloud-only OneDrive, automated organisation/undo, background monitoring, installer, updates, backup/restore and full accessibility acceptance testing.

This is a working local development build, not a production release. Nothing was published. Public research informs the professional context only; no historical email address was treated as verified.

## Account setup follow-up

Added Google Desktop OAuth JSON import and Microsoft public-client ID configuration through Settings. Client configuration is encrypted with Windows DPAPI; environment configuration takes precedence. Tests reject wrong Google client types, invalid IDs and replacing a connected account; provider URLs are fixed rather than taken from uploaded JSON. Google Cloud is awaiting user sign-in. No live credential was imported and no email was sent.

## 14 September 2026 — interface and live Gmail test

- Reworked local home into three task cards, a labelled filename/project search with optional dictation, connected-account status, and grouped recent work. Removed keyword-based intent routing; general AI conversation remains unavailable.
- Gmail OAuth connection observed in Settings. One explicitly authorized test email to the user-supplied recipient, subject `[HARD TEST] Email and PDF attachment verification`, was accepted by Gmail with the fictional one-page proposal PDF. Inbox receipt and attachment opening by the recipient are still unconfirmed. Earlier statements above about no live connection/send describe the previous testing stage.
- Browser recipient check flagged a deliberate extra letter and suggested the exact saved address. Sent record has no Send button.
- Browser home search routed the entered query directly to file search; no folders are configured, so it correctly returned no matches.
- 34 regression tests and JavaScript syntax validation passed.
- Redesigned home and Settings checked at 390px with 200% text: no document horizontal overflow. Restored comfortable text and normal viewport.
- Still pending: Gmail refresh/revocation and delivery-failure tests, Outlook live tests, recipient delivery confirmation, broader document/accessibility testing and the previously listed release blockers. Nothing published.

## AI review implementation — 14 September 2026

The user confirmed that the Gmail test email worked. Opt-in OpenAI document review is implemented with DPAPI-encrypted API setup, fixed Responses endpoint, store=false, a 60,000-character input cap, no tools, bounded structured output, exact quotation checks, refusal/incomplete-response handling, per-request consent, cached local results and no automatic document edits or approval. The saved review is tied to extracted-text hash. No API key was supplied and no real model call has been tested yet.

42 automated tests passed, including 8 new mocked AI tests; JavaScript syntax passed. Live model quality, billing/account access, and representative proposal evaluation remain release blockers. The feature does not verify external facts, page layout or recipient addresses. GPT-4.1 mini is the initial model; it is not a claim of best available model quality. No publishing occurred.

## Windows desktop pilot — 18 September 2026

- Built a 64-bit Windows folder-based executable using an isolated Python environment, pywebview 6.2.1, PyInstaller 6.22.3 and Edge WebView2. Included PowerShell installer creates user desktop and Start menu shortcuts without admin access. Installer has not yet been exercised on the target PC.
- Persistent app data is separate under LocalAppData/HARD Assistant/Data. The pilot ships with no development accounts, keys, contacts or documents. Local service binds 127.0.0.1:5188 and closes with the desktop window. Google/Microsoft sign-in opens the default browser rather than an embedded login.
- 42 existing tests and 2 desktop tests passed. Frozen executable service smoke test and hidden native WebView2 window-load test both exited 0. JavaScript syntax check passed.
- ZIP integrity verified and checked for development data and credential filenames. Third-party notices included, SHA-256 checksum provided.
- Not signed or production ready. Full desktop user-flow acceptance on the uncle's computer remains pending (file dialogs, downloads, OAuth, Word conversion, voice and accessibility). No remote publishing, auto-update service or automatic backup/restore was added. Word/Powershell7/WebView2 prerequisites described in package README. Cloud AI is optional; no local model or subscription-based AI automation is included.

## Inspo UI redesign � 19 September 2026
44 regression tests passed. Browser checked home, document entry, file-search empty state and email composer. Double-size text and 520px viewport had no horizontal overflow; brand mark updated to scale with text. Frozen service and hidden native-window smoke checks passed. ZIP integrity and bundled CSS verified; development data and credential filenames excluded. No live AI test or additional email send.

## Shared pagination — 19 September 2026
10-item pages added to search, documents, folders, contacts, draft history, activity and failure notices. Home previews remain bounded; review issues already use one-at-a-time navigation; native email selects do not grow the page. Removed silent search/document/history caps. Node pagination tests cover 0/1/10/11/17/20/21/101 and all collection renderers. Python regression: 44 passed. Isolated 107-item fixture confirms search/documents/events exceed old caps. Browser Next and new-search reset verified; unsubmitted search input preserved. Desktop rebuilt, installed and service/native-window smoke tests passed. ZIP excludes development data. Inspo consulted; existing HARD tokens retained.

## Profiles and project folders — 19 September 2026
First-run name stored per Windows workspace, editable name/role/notes; new email signatures use profile. Notes are explicit local memory, not automatic AI learning. File type/folder/sort controls and copy-to-project added. Originals preserved; exclusive creation prevents overwrites; path and Windows-name checks. 50 Python tests and pagination checks passed. Browser fictional-name setup survives reload; fictional project copy succeeded. Installed service and native-window smoke passed. No user profile was prefilled and no real files reorganised by QA.

## File/email/provider update — 19 September 2026
60 regression tests passed plus pagination boundary checks. New typed-recipient draft was exercised in the browser using fictional data and no connected email account. Composer and Settings checked at 520px with double-size text: no horizontal overflow. Rename preview, conflict safeguards, undo, content-based duplicates and local reveal route audited. AI provider adapters mocked for OpenAI, Gemini, Anthropic and custom compatibility; no live paid calls. Provider HTTP rejection is failed; network uncertainty stays uncertain without retry. While-open possible-bounce polling added. Build ZIP integrity and exclusion of credentials/data checked; installed service and native-window smoke passed. See UI-AUDIT.md for coverage and remaining release gates.

## Gemini diagnosis and app icon
Live synthetic request confirmed saved model Gemini caused HTTP 400 unexpected model name. Google rejected gemini-2.5-flash for new users and explicitly suggested gemini-3.6-flash. Saved model corrected to that ID. Basic JSON connection test returned HTTP 200; full synthetic review returned Google HTTP 503 high demand. No real document sent in diagnostics. Added exact-model validation and actionable 400/401/403/404/429/503 messages; 63 tests passed. Added original SVG, PNG and multi-size ICO H/water logo, embedded in executable and shortcuts. Installed service/native-window smoke passed. Full live document review remains unverified due to provider availability.


## Ask HARD update — 19 September 2026

- Added session-only general conversation, follow-up context and explicit attachment sharing. Supports DOCX, PDF, TXT, PNG, JPEG and WebP; up to three attachments and 12 MB total. PDFs up to ten pages include rendered pages; longer documents use extracted text.
- All 70 Python tests passed; JavaScript syntax and pagination tests passed.
- Live Gemini request with a generated red-square image succeeded. No personal document sent.
- Browser fixture checks passed for two-turn conversation, imported-document attachment, removal and direct image upload/submission. Mock responses were used for UI checks. 520px layout visually checked with no horizontal overflow.
- Fixed hyphenated data-attribute lookup in UI event binding discovered by document-to-chat check. Captured submitted question independently of subsequent typing.
- Packaged ZIP integrity and personal-data exclusion checks passed. Installed after user confirmed app closed. Both installed --smoke-test and --window-smoke returned zero; installed JavaScript matched source.
- Chat has no web browsing or action tools and does not send emails or alter files. History clears on close/reload; API/model capabilities and provider availability apply. Pilot remains unsigned and unpublished.


## Minimal dashboard — 19 September 2026
- Replaced large coloured task tiles with one Ask HARD panel and three compact shortcuts. Recent work collapsed by default. Sharing consent stays visible; help expands on demand.
- Normal page scrollbar; conversation no longer traps scrolling in an inner panel.
- Browser checked at widths 320, 520 (double-sized text), 768, 1100 and 1920. No horizontal overflow. Desktop and narrow layouts visually inspected.
- All three shortcuts, recent-work disclosure and mock chat submission passed. JavaScript syntax and existing pagination suite passed.
- Minimal-Dashboard ZIP integrity and personal-data exclusion checks passed.


## Sidebar and durable chats — 19 September 2026
- Used Inspo MCP ChatGPT reference for a chat-first sidebar layout. Workflows moved to sidebar; recent eight chats and paginated full history. Narrow screens use a collapsible menu.
- SQLite conversations and turns retain messages, failures and attachment snapshots across restarts. Server supplies recent completed context. Per-request deduplication prevents a repeated request ID from invoking the provider again. Rename and explicit deletion supported.
- 77 tests passed, plus JavaScript syntax and pagination. Seven storage tests rerun after final efficiency/concurrency changes. Browser mock conversation created, page reloaded and conversation successfully reopened; mobile menu/history and 520px double-text layout checked without horizontal overflow.
- Built executable passed startup and native window smoke checks. Distribution ZIP passed integrity and personal-data exclusion checks. Installation pending user close confirmation.

Saved-chat update installed after user confirmed HARD was closed. Installed executable and UI assets matched release; installed --smoke-test and --window-smoke both returned zero.


## Dictation fix
- Desktop button uses Windows voice typing via Win+H, with message focus and foreground-process guard. Native key releases are attempted on SendInput failure. CSRF-protected desktop-only endpoint.
- Browser recognition retained with specific errors, stop control, insertion at cursor and state synchronization; does not overwrite edits made while listening.
- 80 Python tests passed; dictation JavaScript behavior and pagination checks passed. Packaged desktop startup/window smoke checks and ZIP integrity passed.
- Real microphone transcription has not been tested; user validation required after installation. Windows handles speech processing and microphone permissions.

Dictation fix installed after user close confirmation; installed assets matched build and both startup checks passed.


## Formatted answers, fixed composer and saved AI connections — 20 September 2026
- Used Inspo ChatGPT reference for a fixed composer and separately scrolling conversation. Markdown-it 15.0.2 and DOMPurify 3.4.15 render headings, lists, tables and code locally; raw HTML, unsafe links and remote images are blocked. Libraries and licenses are bundled.
- Multiple named connections are encrypted for the Windows account in ai.connections. Legacy configuration is preserved. The composer selects the active connection; stale connection IDs are rejected before a provider request.
- Chat uses explicit Send with a visible destination/sharing notice, replacing the repeated checkbox. Cloud inference still transmits the message, recent context and selected files to the chosen provider. No offline AI added.
- 84 Python tests passed; Markdown safety/structure, dictation UI, JavaScript syntax and pagination checks passed. Isolated browser test saved and selected a second connection. Long formatted response showed a fixed composer with a scrolling log and no page scrolling. Checked desktop, 320px width and 520px double text; small/high-zoom composer panels may scroll internally for accessibility. No personal content sent in these checks.

Formatted-chat update packaged and installed while HARD was closed. Installed executable and six UI assets matched release/source. Both installed startup checks passed. Existing user Data folder preserved by installer.


## Chat sharing and action menu — 20 September 2026
- Share chat offers standalone HTML export and clipboard text. No hosted link or automatic external sending; excludes attachment binaries, stored keys and account details. Message content may still contain private information.
- Compact floating three-dot menu, outside-click dismissal, keyboard navigation/Escape, focus management; composer position unchanged while open. Pill-shaped buttons, restrained hover motion and reduced-motion support.
- Share-export DOM tests passed for formatting, HTML escaping, script/image blocking and exclusion of attachment data/credentials. Markdown and pagination regression suites passed. Browser verified desktop menu/share dialog, download request and 320px dialog. Actual recipient delivery not attempted.
- ZIP integrity/exclusion checks passed. Installed while HARD was closed; installed assets matched source; both installed startup checks passed.


## OpenRouter model discovery - 20 September 2026
- Public model catalog fetched without credentials or chat data. Text-output models, search, image filter, 15-minute cache, refresh and stale-cache fallback. Existing official-endpoint custom connections supported. Selection preserves the key and rejects stale connection IDs.
- 88 Python tests passed plus formatting, sharing, dictation, pagination and syntax checks. Live catalog returned 428 models. Browser verified search, selection and image filtering; bounded list at 520px with no horizontal overflow. No AI messages sent.
- ZIP integrity and credential exclusions passed. Installed while HARD was closed; installed executable and assets matched release. Both installed startup checks passed. User data preserved. Catalog availability does not guarantee model access or task compatibility.


## Composer focus and keyboard shortcuts - 20 September 2026
- Rounded composer focus indicator replaces the rectangular textarea outline; other control focus indicators and forced-colors support preserved. Visible and screen-reader-associated keyboard hint. Enter/Ctrl+Enter submit through the same validated form flow as Send; Shift+Enter inserts a newline. Guards for IME composition, repeated keys, busy state, blank input and missing configuration.
- Shortcut unit checks, JavaScript syntax, dictation and pagination checks passed. Isolated browser confirmed Shift+Enter newline, Enter submission using a local mock response, and rounded parent focus with no inner textarea outline.

Shortcut update installed after user close confirmation. Installed UI assets matched source. Both installed startup checks and package integrity passed. Reopened HARD; user data preserved.


## Previews, reading and conversions - 21 September 2026
- Hidden visible shortcut hint while preserving accessible description; restored company name; green focus across controls with forced-colors support. Settings height transitions respect reduced motion.
- Local attachment cards and modal previews: normalized images, first 3 PDF page images, escaped Word/text preview. Explicit no-network preview endpoint.
- Direct DOCX-to-PDF control uses existing installed Word flow without implying review approval. Added PDF-to-DOCX editable text conversion with page breaks, scanned-page warnings, 100-page/character bounds, original preservation and no automatic approval. Original layouts/images/tables are not reconstructed.
- Read aloud selects latest answer only, omits code and controls; selectable local voices and speed. HARD identity clarified in AI instructions.
- 88 regression tests and 7 new preview/conversion tests passed, plus shortcut, pagination, dictation, sharing and reading JS checks. Actual synthetic PDF converted into valid DOCX. Browser image/Word preview, visible cards, branding and settings open/close verified.
- Desktop build and both startup checks passed; ZIP integrity and credential exclusion checks passed. Desktop Word not detected, so actual DOCX-to-PDF not verified on this PC. Audible voice quality still requires user listening.

Installed after user close confirmation. Installed executable/UI matched release; installed startup and window checks passed. Existing user data preserved.


## Message clipboard controls - 21 September 2026
- Copy selected text or entire draft, cut selected text only after a successful clipboard write, paste at saved cursor/selection. Preserve edits on async races and reject over-limit pastes. Native keyboard shortcuts remain available if Clipboard API is blocked. Company name moved outside the composer, with a separate grid row.
- Clipboard behavior, keyboard submission, pagination and syntax checks passed.

Clipboard update installed after close confirmation. Installed assets matched source; both desktop startup checks passed. Browser confirmed caption is outside and below composer.


## Image clipboard paste - 21 September 2026
- Removed Copy/Cut/Paste toolbar. Native text shortcuts preserved. Pasted PNG/JPEG/WebP clipboard files attach via the same encoding and local preview path as uploads; item fallback supported. Unsupported image formats and busy state produce guidance. No clipboard polling or background reads.
- Paste behavior tests, actual FileReader/preview integration with mock preview endpoint, 3-file/12 MB limits, keyboard submission, pagination and syntax checks passed.

Installed while HARD was closed; installed UI assets matched source and both startup checks passed.


## Failed answer recovery - 21 September 2026
- Consulted Inspo ChatGPT composition reference; kept recovery actions inline under the error using existing design tokens. Retry answer uses original saved question/files, replaces the failed turn, limits history to earlier completed turns, rejects already-complete/wrong-chat requests and prevents concurrent sends. Current selected provider/model is displayed. Edit message restores text/files with unsent-draft confirmation.
- 99 Python tests passed; keyboard, sharing, pagination and syntax checks passed. Isolated browser verified Edit restoration and Retry failure-to-success: one question, one answer, no error, unsent draft preserved. No real AI request sent.


## Email connection vs delivery failure - 21 September 2026
- Live Gmail profile read succeeded. The 17 September notice reports Action failed, Status 5.1.3, nonexistent recipient. No email resent and no credentials exposed.
- Delivery screen now distinguishes successful inbox access from a past message delivery notice. On-demand Gmail diagnostic parsing displays structured DSN fields, excludes original message bodies, validates IDs and escapes text in the UI.
- Global Graft preference saved in the user AGENTS.md. HARD graph built locally with telemetry disabled; separate skill not installed, existing CLI used.

Combined retry/email-status build installed while HARD was closed. Package integrity, installed file match and installed startup/window checks passed. Graft graph refreshed.


## Delivery inbox and handled notices - 21 September 2026
- Inspo Linear reference informed compact status/action hierarchy within HARD colors. New compact banner, attention/handled views, Check now, quieter status badge and collapsible diagnostic content. Banner omitted on the delivery inbox itself.
- SQLite notice history scoped by provider/account and message ID. Handled state survives restarts and scan-window expiry; new IDs still alert. Restore supported, account isolation tested. Emails are not altered.
- 13 targeted email tests and pagination checks passed. Browser verified marking a notice handled removes it from attention.

Installed while HARD was closed; installed files matched release, ZIP integrity and desktop smoke checks passed. The specific resolved 17 September notice was marked handled after matching its diagnostic recipient. Gmail contents unchanged.

2026-09-21: Optional OpenRouter public web search with capped server searches, saved citations and retry mode. 108 Python tests passed. Live public UN-Water query succeeded with three citation URLs. No database access added.

2026-09-29 v0.2.0: 119 Python tests, 8 interface test files, 6 isolated Playwright browser journeys passed. Tested backup integrity, restoration, credential exclusion, guarded copy/move/rename undo, recovery after reload, email typo preflight, model switching, narrow viewport, installer startup rollback and workspace preservation. Packaged service and window smoke checks passed. Live Word/email/hardware acceptance remains separate.
