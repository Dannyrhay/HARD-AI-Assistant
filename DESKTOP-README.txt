HARD Assistant — Windows desktop pilot

This is an unsigned test build, not a production release.

SETUP
1. Extract the complete ZIP to a folder on the Windows PC.
2. Right-click Install-HARD.ps1 and choose Run with PowerShell. No administrator access is required. If organisation policy blocks scripts, ask its administrator; do not weaken policy.
3. Open the HARD Assistant desktop shortcut. Alternatively run HARD Assistant/HARD Assistant.exe directly after extracting the ZIP.

REQUIREMENTS
64-bit Windows 10/11 and Microsoft Edge WebView2 Runtime. If the window cannot open, get WebView2 from https://developer.microsoft.com/microsoft-edge/webview2/ .
PDF conversion additionally requires activated desktop Microsoft Word and PowerShell 7 (https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows). These are not bundled. Basic file review does not require an AI subscription or API key.

YOUR UNCLE'S FIRST RUN
The package contains NO account credentials, test documents or saved contacts. In Settings, import your Google Desktop client JSON and connect his own Gmail account. Add his exact address as a Google test user first. OAuth sign-in opens the default browser: return to HARD and select Settings to refresh after signing in. Keep HARD open throughout sign-in. Outlook requires separate application setup. AI API review is optional and separately billed. ChatGPT Pro does not supply API credit.
Choose specific work folders in Settings. OneDrive files must be downloaded locally. Verify contacts against the original client request. Never treat AI suggestions as factual approval.

DATA
User data: %LOCALAPPDATA%/HARD Assistant/Data
Desktop browser preferences: %LOCALAPPDATA%/HARD Assistant/Browser
Application files: %LOCALAPPDATA%/Programs/HARD Assistant (if installed)
To back up, close HARD and copy the whole Data folder to a protected backup location. Tokens/keys are encrypted for the Windows account and cannot simply be transferred to another PC; reconnect accounts there. Automatic backup/restore is not included.

NETWORK
The app runs on this PC and binds only to 127.0.0.1:5188. Do not expose this port to a network. Email and cloud AI require internet. Closing HARD stops its local service. Avoid closing during conversion or sending. Do not run the development server at the same time.

LIMITATIONS
This pilot still needs target-machine testing: file picker/downloads, Word conversion, Gmail sign-in, accessibility, microphone and reading aloud. No automatic updates, code signing or local language model are included. AI reviews and chat share selected content only after confirmation. No website hosting is needed.

UPDATES / REMOVAL
Close HARD before installing a replacement package. Application updates preserve the separate Data folder. To remove this pilot, delete its application folder and shortcuts; keep the Data folder until your backups are verified. No automatic update service is installed.

FILE AND EMAIL UPDATE
Find a file supports type/folder filters, sorting, Show in folder, project copies, rename with session undo, and exact-content duplicate checks. Renaming changes the original filename; project organisation copies and preserves the original. Duplicate detection never deletes files. Review copies remain separate.
Email supports saved or manually entered recipients. A typed address is confirmed for that message, not automatically saved or certified as an existing mailbox. Review the draft before sending. HARD checks for possible delivery notices every five minutes while open, and prompts on failures or uncertain sends. Checks can miss notices and do not prove delivery; check the actual inbox. No checks run after HARD closes.
AI setup supports OpenAI Responses, Gemini Chat Completions compatibility, Anthropic Messages and custom HTTPS OpenAI-compatible Chat Completions services using bearer keys and JSON output. Supply the provider's model ID and, for custom services, its full chat/completions URL. Keys are encrypted for the current Windows account. Provider capabilities, billing and retention differ; not every API key or model is compatible. No live calls were verified without user credentials.

ASK HARD
The home composer supports questions, follow-ups, and up to three selected DOCX/PDF/TXT/PNG/JPEG/WebP attachments (12 MB combined, 60,000 extracted characters). PDFs up to 10 pages include page images; larger PDFs use text only, and long scanned PDFs need smaller sections. Image understanding requires a vision-capable model. Sending shares the question, up to 12 recent messages and current attachments with the selected provider. Sent conversations and attachment copies are saved locally in the Data folder. Reopen them from Recent chats or All chat history in the sidebar. Chat options allow rename and deletion; original files remain unchanged. Unsent text is not saved. Saved history is not separately encrypted; it uses the same Windows-account workspace as your imported documents. Document review has an Ask HARD shortcut. Chat cannot execute file operations, send messages or browse the web; use the explicit app workflows for actions.

DICTATION
Desktop Dictate focuses the message and opens Windows voice typing (Windows + H). Windows handles microphone access and speech processing; internet access and a working microphone are required. Stop using the microphone control in the Windows voice typing panel. Review text before sending. HARD does not send raw audio to the configured AI provider. If the panel fails, focus the message and press Windows + H manually; check Windows Sound input and microphone privacy settings.

FORMATTED CHAT AND AI CONNECTIONS
Answers render locally as safe Markdown; raw HTML and remote images are disabled. The chat view scrolls independently of the anchored composer. On very small windows or large text settings, composer controls may scroll within their panel to remain accessible.
Save multiple named AI connections in Settings and select one beside Send. Keys are encrypted for the Windows account in ai.connections; existing setup is preserved. Document review uses the active connection.
Send replaces the chat checkbox: the destination is displayed with a sharing notice. Sending transmits the message, recent conversation and selected attachments to that cloud provider. Switching alone sends no chat content. Local storage does not mean cloud inference is private or offline. Provider data policies depend on account, region and service terms.

SHARE A CHAT
Open a saved conversation, choose the three-dot Chat options button, then Share chat. Download a standalone HTML snapshot or copy the conversation text. Send the file/text using your preferred email or messaging app. Attachment files, API keys and account settings are not included; the messages themselves may contain confidential details. No public link is created and nothing is automatically sent to another person.

OPENROUTER MODELS
Choose OpenRouter in Settings to load model suggestions automatically. Existing custom connections using the official OpenRouter endpoint also support the Models button beside Send. Search the public catalog, optionally filter for image input, select a model and choose Use selected model. The same encrypted API key is retained. Catalog fetching sends no key or chat content; it is cached for 15 minutes, with Refresh list available. Saved models still work when the catalog is unavailable. Catalog listings do not guarantee account access or compatibility with every task.

CHAT KEYBOARD
Enter sends your message. Shift+Enter inserts a new line. Ctrl+Enter also sends. While an answer is processing, submission is blocked to prevent duplicates. A rounded green outline shows focus within the composer.

PREVIEWS, CONVERSIONS AND READING
Attachments appear above the message as cards. Click to preview locally: image thumbnails, first three PDF pages, or Word/text content. Previewing sends nothing to AI. Word to PDF is available directly after importing a DOCX in Documents and uses installed, activated desktop Word. PDF to Word creates an editable text copy, preserving page breaks but not original layout, tables or images; image-only scans require OCR. Original files remain unchanged and converted copies still need review.
Read aloud speaks the latest HARD answer, skipping interface controls and code. Choose an installed voice and speed under Settings / Reading comfort. Local English voices are preferred; online voices may use a speech service. Voice quality depends on the installed voices.

FAILED ANSWERS
Retry answer under a failed response resends the saved message and original attachment copies using the connection and model currently shown. A successful reply replaces the error; your unsent draft is preserved. Edit message restores the text and files to the composer for changes; Send then creates a new message. No automatic retry loop runs. Provider costs and availability still apply.

DELIVERY INBOX
Mark a delivery notice as handled after you resolve it. HARD remembers this for the connected account and stops repeating its alert. Handled history stays on this PC and lets you move a notice back to attention. New notice IDs still alert even for the same recipient. No email is deleted, changed or resent. Check now refreshes the scan; regular checks run every five minutes while HARD is open.
