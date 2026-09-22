# HARD Assistant

A local Windows assistant for Dr Stephen Maxwell Donkor, Holland Africa Research & Development.

**Release status: development build, not production-ready. Do not publish the static directory as a working application.** The interface now depends on the local Python service. No accounts, credentials or original user folders are preconfigured.

## Start locally

Requires Python 3.12+, the packages in requirements.txt, Windows desktop Word activated for PDF export, and PowerShell 7 (the tested conversion runtime).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Open http://127.0.0.1:5188. Keep the service running. It binds only to loopback. Do not expose this service through a public tunnel or deploy it to a web host. Current desktop development uses the Codex bundled Python runtime with the same dependency versions.

## Implemented

- Minimal home screen: one typed request and three actions; no sidebar. Adjustable 20/24/28/40px text, keyboard focus, optional browser dictation and read-aloud.
- Import actual DOCX/PDF/UTF-8 text, read without overwriting originals, deduplicate imported content by SHA-256, save versioned corrections and reviews in SQLite.
- Explicitly selected folder indexing, including locally synced OneDrive folders; no whole-drive scans. Overlapping roots and symlink/junction traversal are rejected or skipped. Indexing is limited to 10,000 files; search returns the first 100 matches.
- Mechanical document checks for placeholders, repeated words, comments, tracked changes, multiple currencies and email addresses. These checks do not certify facts, spelling, grammar or arithmetic.
- Exact single-occurrence corrections in supported Word runs/body/table paragraphs, preserving other formatting. Complex edits fail explicitly and require Word. Revisions are separate documents.
- Word PDF export with macro execution and link updates disabled; PDF parsing/page checks and a coarse extracted-text comparison. User must inspect and approve actual PDF pages before preparing email.
- Manually verified contacts with a source note; typed-address comparison suggests similar saved addresses but never silently substitutes one.
- Durable immutable email drafts, real EML download with the exact PDF attachment, approval-bound sender check and attachment hash check. The send service uses a single-attempt state transition; network uncertainty prevents automatic resend.
- Gmail and Outlook OAuth adapters using PKCE/state validation and Windows DPAPI-encrypted token storage. These are implemented but **not live-tested**. Gmail reports sent only after a provider receipt; Outlook reports accepted. Neither status means delivered.
- On-demand possible delivery-notice search for connected accounts, explicitly not exhaustive and not background monitoring.
- Host/Origin/CSRF checks; no CORS; static asset allowlist; private database and tokens never served as static files. No request-body or OAuth-code logging.

## Account setup required before integration tests

Do not paste client secrets or tokens into chat. Use Settings → Application setup to import a Google Desktop OAuth JSON file or enter a Microsoft public-client application ID. HARD validates the client type and encrypts the minimal configuration with Windows DPAPI. Existing account connections must be disconnected before replacing their configuration. Alternatively configure environment variables in the process that starts HARD; these take precedence. `.env` files are ignored but not automatically loaded.

### Gmail

Create a Google Cloud Desktop OAuth client for this application, enable Gmail API, and configure the consent/testing audience. Set `HARD_GOOGLE_CLIENT_ID` and, when supplied with the desktop client, `HARD_GOOGLE_CLIENT_SECRET`. Sign in from HARD Settings. Redirect: `http://127.0.0.1:5188/oauth/callback` using the desktop loopback flow. Scopes: Gmail send and readonly. Verification and publishing requirements depend on the Google project/audience and must be resolved before release. Test with a dedicated account and explicitly approved test recipients.

### Outlook

Register a Microsoft identity desktop/public-client application supporting the intended account type. Configure the loopback redirect `http://127.0.0.1:5188/oauth/callback`, delegated `User.Read`, `Mail.Read`, `Mail.Send` and offline access. Set `HARD_MICROSOFT_CLIENT_ID`. Do not embed a secret in a distributed public client. Outlook files over 3 MB currently require finishing in Outlook; the large-attachment upload workflow is not implemented.

Disconnect removes HARD's saved local token. It does not revoke the provider's server-side grant; revoke that in Google/Microsoft account permissions if needed.

## Data and recovery

`.data/` contains copied documents, review notes, contacts, drafts and audit events. Tokens are encrypted for the current Windows user. The documents/database are local plaintext protected by the Windows account/filesystem; no application-level encryption, backup schedule or installer has been implemented. Back up `.data` only while HARD is stopped. Never include `.data`, `.test-data`, tokens or OAuth credentials in source control or hosting archives.

Test fixtures are fictional and stored in `.test-data/`. Isolated automated tests use temporary directories. Do not confuse test accounts/contacts with Dr Donkor's real contacts. Reopening an in-flight send after a crash marks it uncertain; inspect the provider's Sent folder before deciding what to do.

## Verification

```powershell
python -m unittest test_hard -v
node --check dist/app.js
```

Tests exercise file boundaries, original preservation, duplicate import, review gates, durable drafts, attachment integrity, contact validation, CSRF/Host checks, DPAPI round trip, single-attempt sending and uncertain-send handling. Provider requests in send tests are mocked; no real email is sent.

## Required before production

1. Live Google and Microsoft OAuth/token-refresh/revocation tests and approved send/receive/failure-message tests.
2. AI provider selection, data-transmission consent, factual/linguistic review implementation and evaluation using representative water-consultancy documents.
3. Cloud-only OneDrive integration, OCR if needed, controlled file organisation with preview/undo, and durable background delivery monitoring.
4. Representative Word layout tests (tables, annexes, fonts, images, headers, footnotes), timeout/process cleanup and locked-file recovery on Dr Donkor's computer.
5. Packaging, updates, data protection, backup/restore, dependency/security review, and accessibility acceptance testing with Dr Donkor.
6. Complete manual release checks; do not label this build production-ready until these gates pass.

## Research grounding

- UN-hosted African Water Development Report presentation names Stephen Maxwell Donkor and UNECA: https://sustainabledevelopment.un.org/content/documents/3225donkor.pdf
- UNECA 2019 forum page lists his water/sanitation work: https://archive.uneca.org/arfsd2019/pages/arfsd2019-presentations
- Public self-published CV names Holland Africa Research & Development: https://independent.academia.edu/StephenDonkor/CurriculumVitae

Historical contact addresses, dates of birth and private details are not imported into the application.

## Integration references

- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send
- https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat


### AI document review (requires live setup)
In Settings > AI document review > AI setup, enter an OpenAI API key with API billing enabled. It is encrypted locally with Windows DPAPI. Alternatively set HARD_OPENAI_API_KEY for the local process. Saving a key does not verify it. No credentials go into browser storage or source code.

Open a document, read the sharing notice, then request an AI second opinion. Only its extracted text is sent to OpenAI, with store=false (this does not mean zero provider retention). API charges apply. Inputs over 60,000 characters are rejected rather than silently truncated. Existing saved results are reused. Suggestions are displayed separately and do not edit files, decide review items, or approve documents. AI can miss problems or make incorrect suggestions. Live API and quality testing remains required before release.

### Public web search
Choose an OpenRouter connection and turn Web on beside Send. Off by default. Queries may include conversation details and are shared with an external search engine; search charges may apply. Each answer permits at most two Exa searches, three results per search. Sources are saved with chat history; no-source responses are explicitly labelled. Other direct provider connections do not yet offer this switch. Retry preserves the original Web setting; Edit message allows changing it.
