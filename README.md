# HARD Assistant

HARD (Holland Africa Research & Development) is a local Windows AI assistant for managing documents, finding files, preparing emails and getting help through chat. It supports individual users and professionals across different fields, with a profile each user can personalise.

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

- Chat workspace with a sidebar for documents, files, email and saved conversations. Adjustable 20/24/28/40px text, keyboard focus, optional browser dictation and read-aloud.
- Import actual DOCX/PDF/UTF-8 text, read without overwriting originals, deduplicate imported content by SHA-256, save versioned corrections and reviews in SQLite.
- Explicitly selected folder indexing, including locally synced OneDrive folders; no whole-drive scans. Overlapping roots and symlink/junction traversal are rejected or skipped. Indexing is limited to 10,000 files; results are displayed in pages of ten.
- Mechanical document checks for placeholders, repeated words, comments, tracked changes, multiple currencies and email addresses. These checks do not certify facts, spelling, grammar or arithmetic.
- Exact single-occurrence corrections in supported Word runs/body/table paragraphs, preserving other formatting. Complex edits fail explicitly and require Word. Revisions are separate documents.
- Word PDF export with macro execution and link updates disabled; PDF parsing/page checks and a coarse extracted-text comparison. User must inspect and approve actual PDF pages before preparing email.
- Manually verified contacts with a source note; typed-address comparison suggests similar saved addresses but never silently substitutes one.
- Durable immutable email drafts, real EML download with the exact PDF attachment, approval-bound sender check and attachment hash check. The send service uses a single-attempt state transition; network uncertainty prevents automatic resend.
- Gmail and Outlook OAuth adapters using PKCE/state validation and Windows DPAPI-encrypted token storage. Gmail has passed a development send test; OAuth refresh, revocation and Outlook still require live acceptance testing. Gmail reports sent only after a provider receipt; Outlook reports accepted. Neither status means delivered.
- Delivery-notice checks for connected accounts run every five minutes while HARD is open. Handled notices stay dismissed; results are not exhaustive.
- Host/Origin/CSRF checks; no CORS; static asset allowlist; private database and tokens never served as static files. No request-body or OAuth-code logging.

## Account setup required before integration tests

Do not paste client secrets or tokens into chat. Use Settings → Application setup to import a Google Desktop OAuth JSON file or enter a Microsoft public-client application ID. HARD validates the client type and encrypts the minimal configuration with Windows DPAPI. Existing account connections must be disconnected before replacing their configuration. Alternatively configure environment variables in the process that starts HARD; these take precedence. `.env` files are ignored but not automatically loaded.

### Gmail

Create a Google Cloud Desktop OAuth client for this application, enable Gmail API, and configure the consent/testing audience. Set `HARD_GOOGLE_CLIENT_ID` and, when supplied with the desktop client, `HARD_GOOGLE_CLIENT_SECRET`. Sign in from HARD Settings. Redirect: `http://127.0.0.1:5188/oauth/callback` using the desktop loopback flow. Scopes: Gmail send and readonly. Verification and publishing requirements depend on the Google project/audience and must be resolved before release. Test with a dedicated account and explicitly approved test recipients.

### Outlook

Register a Microsoft identity desktop/public-client application supporting the intended account type. Configure the loopback redirect `http://127.0.0.1:5188/oauth/callback`, delegated `User.Read`, `Mail.Read`, `Mail.Send` and offline access. Set `HARD_MICROSOFT_CLIENT_ID`. Do not embed a secret in a distributed public client. Outlook files over 3 MB currently require finishing in Outlook; the large-attachment upload workflow is not implemented.

Disconnect removes HARD's saved local token. It does not revoke the provider's server-side grant; revoke that in Google/Microsoft account permissions if needed.

## Data and recovery

`.data/` contains copied documents, review notes, contacts, drafts and audit events. Tokens are encrypted for the current Windows user. The documents/database are local plaintext protected by the Windows account/filesystem; there is no application-level encryption or scheduled backup. Version 0.2.0 provides manual backup/restore and a Windows installer. Back up `.data` only while HARD is stopped. Never include `.data`, `.test-data`, tokens or OAuth credentials in source control or hosting archives.

Test fixtures are fictional and stored in `.test-data/`. Isolated automated tests use temporary directories. Keep fictional test accounts and contacts separate from real user data. Reopening an in-flight send after a crash marks it uncertain; inspect the provider's Sent folder before deciding what to do.

## Verification

```powershell
python -m unittest test_hard -v
node --check dist/app.js
```

Tests exercise file boundaries, original preservation, duplicate import, review gates, durable drafts, attachment integrity, contact validation, CSRF/Host checks, DPAPI round trip, single-attempt sending and uncertain-send handling. Provider requests in send tests are mocked; no real email is sent.

## Required before production

1. Live Google and Microsoft OAuth/token-refresh/revocation tests and approved send/receive/failure-message tests.
2. AI provider selection, data-transmission consent, factual/linguistic review implementation and evaluation using representative documents from the intended use cases.
3. Cloud-only OneDrive integration, OCR if needed, controlled file organisation with preview/undo, and durable background delivery monitoring.
4. Representative Word layout tests (tables, annexes, fonts, images, headers, footnotes), timeout/process cleanup and locked-file recovery on supported Windows devices.
5. Packaging, updates, data protection, backup/restore, dependency/security review, and accessibility acceptance testing with representative users, including people with low vision.
6. Complete manual release checks; do not label this build production-ready until these gates pass.

## Integration references

- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send
- https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat


### AI document review (requires live setup)
In Settings > AI document review > AI setup, enter an OpenAI API key with API billing enabled. It is encrypted locally with Windows DPAPI. Alternatively set HARD_OPENAI_API_KEY for the local process. Saving a key does not verify it. No credentials go into browser storage or source code.

Open a document, read the sharing notice, then request an AI second opinion. Only its extracted text is sent to OpenAI, with store=false (this does not mean zero provider retention). API charges apply. Inputs over 60,000 characters are rejected rather than silently truncated. Existing saved results are reused. Suggestions are displayed separately and do not edit files, decide review items, or approve documents. AI can miss problems or make incorrect suggestions. Live API and quality testing remains required before release.

### Public web search
Choose an OpenRouter connection and turn Web on beside Send. Off by default. Queries may include conversation details and are shared with an external search engine; search charges may apply. Each answer permits at most two Exa searches, three results per search. Sources are saved with chat history; no-source responses are explicitly labelled. Other direct provider connections do not yet offer this switch. Retry preserves the original Web setting; Edit message allows changing it.

## Continuous integration

[![HARD CI](https://github.com/Dannyrhay/HARD-AI-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Dannyrhay/HARD-AI-Assistant/actions/workflows/ci.yml)

Every push and pull request runs the Python suite and all `test_*.cjs` interface checks on Windows, builds the desktop executable, and checks the packaged local service starts successfully. Runs can also be started manually in Actions. CI uses synthetic data and mocked providers; no API keys or mailbox credentials are required.

To run interface checks locally, install Node.js 24, run `npm ci`, then `npm test`. Python tests use `./.desktop-venv/Scripts/python.exe -m unittest discover -v` after installing `requirements-desktop-lock.txt` into that environment.

CI does not verify live email delivery, paid AI calls, microphone hardware, the interactive desktop window or activated Microsoft Word conversion. Those still require desktop acceptance checks.

## Version 0.2.0: local workflows and recovery

- Ask chat to find files, prepare an email, review a document or convert a file. Supported requests show local action buttons. They do not call an AI provider or send email automatically. General questions still use the selected provider.
- Organise files with a destination preview. Copy preserves the original; move supports destinations on the same drive. Copies, moves and renames have persistent undo under Find a file. Undo checks content hashes and refuses changed files or name collisions. Duplicate review compares file contents without deleting files.
- Email preflight flags unfamiliar addresses, similar contacts, common domain typos, placeholders and named attachments that are not included. It does not prove an address exists. Every email still requires PDF review and a final sending approval; uncertain sends are never retried automatically.
- The current unsent chat (including attachments) and email form are saved locally shortly after editing and restored after restart. Recipient and PDF approval checkboxes must be checked again. Drafts are local plaintext, like the rest of the workspace.
- Settings > Backups and updates downloads a validated backup of chats, contacts, drafts and imported documents (up to 512 MB). Backups are unencrypted and exclude API keys and account credentials. They do not include original files in external work folders. Close HARD and run `Restore-HARD.ps1` to restore a trusted backup; the prior Data folder is retained. Reselect work folders after restoring. File undo from a restored backup is disabled to protect current external files.
- The installer stages new files, checks their hashes and verifies startup before removing the previous application. A failed startup restores the previous installation. Workspace data remains separate. Updates are manual; the Settings link opens GitHub Releases, where an installer must be published before it is available to other users.

Run `npx playwright install chromium` and `npm run test:e2e` for isolated browser journeys. CI includes these tests. They use temporary workspaces and simulated providers, never personal files or real mailboxes.
