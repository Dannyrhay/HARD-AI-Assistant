# HARD UI and workflow audit
19 September 2026

Inspo consulted for calm light narrative-workflow composition. Adopted grouped recipient/message/attachment surfaces, clear review steps, restrained evergreen styling and readable controls. Kept the existing HARD identity. Source reference returned: https://flatfile.io/ .

Reviewed home, welcome, documents, review, file search, organise, rename, duplicates, email preparation, draft review, settings, history and delivery status. Shared ten-item pagination retained. Settings panels collapse separately. Long text wraps; email/Settings checked at 520px and double-size text. Draft creation with a new fictional recipient verified without sending. Unfinished forms warn before normal in-app navigation. No duplicate deletion or unsolicited real-file changes in QA.

Provider reference docs:
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://ai.google.dev/gemini-api/docs/openai
- https://platform.claude.com/docs/en/api/messages/create

Verification: 60 Python tests plus pagination checks; adapter requests mocked, not live account certification. Core tests cover no automatic retry, sender/attachment approval, exact quotes, malformed responses, encrypted credentials, typed-address checks, rename conflicts/undo and duplicate contents. Delivery checks report possible notices, not definitive per-message delivery status. Live API/provider access, real bounced-mail detection, signing and target-machine acceptance remain release gates.
