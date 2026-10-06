# Security boundary

This is an authenticated, loopback-only learning app. It is not an internet
deployment or a guarantee of zero data leaks.

## Account and chat isolation

The server binds to `127.0.0.1:8001`. Scrypt password hashes have unique salts.
Random opaque cookies are HttpOnly/SameSite=Strict and stored server-side as
SHA-256 digests. The server selects the account identity; request bodies and
query strings cannot select another user's conversation. Each login has a
separate in-memory history and matching CSRF token. Host and origin checks
reject cross-site requests; API/debug/chat-list endpoints are not exposed.

History is capped at 24 messages, expires after 15 minutes idle / 30 minutes
absolute, and is swept every 30 seconds. Clear-chat removes the history after
any active generation. Logout revokes the session immediately, so late model
results cannot restore a logged-out chat. An ADK session is created for each
generation and deleted afterwards. Only up to 12 accepted recent messages from
the current login are sent as model context. Refused raw messages are not saved
or added to the planner's accepted context.

## Guardrails

Local checks catch recognizable keys, contact details, identity numbers, and
obvious instruction attacks. A Gemini intent check allows natural itinerary
requests, any destination and hotel preference, and relevant follow-up questions.
The main ADK agent has travel-only instructions and a response schema. Its reply
is checked for recognizable secrets, schema validity, and itinerary scope before
display. Model thoughts are removed. Extra JSON fields are rejected locally,
even when the transport schema omits unsupported schema keywords for compatibility.

Scope/secret detection is best effort and can make mistakes. The app does not
claim to detect every prompt injection or all PII. Semantic checks depend on the
configured model; a failed check does not disable the guardrail or select an
offline fallback. No model tool can read accounts, other chats, files, shell,
browser contents, or booking systems. Privacy access control is independent of
model decisions and enforced by the API/session store.

## Data sent outside the computer

Messages that pass the local checks, and recent accepted travel context, are
sent to Google Gemini for intent checking and itinerary generation. The generated
answer is also sent to Gemini for output review. An off-topic message may be sent
to the intent checker even when the planner refuses it. Free text allows richer
planning but may contain details the heuristics do not recognize; do not enter
personal secrets or sensitive information. Google processing/retention is outside
this app's control. There is no app tracing or payload logging in the supported
launcher. Private chat exports remain ordinary files on your computer.

## Other controls and limits

- 8192 request bytes, 4000 chat characters; bounded schema string lengths.
- 100 active login sessions; 120 API requests/client/minute.
- Login: 10 attempts/client/minute, 5 per username/minute.
- Chat: 10 requests/account/minute and 30 AI attempts/account/hour.
- Three simultaneous AI tasks; bounded call counts, retries, and timeouts.
- Model-generated prices are estimates; Python sums cost categories exactly.
- All model text is inserted as text nodes, never HTML. No browser chat storage.
- Generic error messages exclude SDK payloads, keys, prompts, and account details.

Someone controlling the OS account, process, browser profile, or an unlocked
signed-in browser can access local data. Windows files inherit OS folder ACLs;
Unix file modes do not configure Windows ACLs. HTTP cookies lack Secure only
because this app is loopback-only. An internet deployment requires HTTPS/Secure
cookies, managed authentication, shared stores, privacy review, and security
testing. Do not expose this prototype by changing its host to `0.0.0.0`.

Keep `.env`, `.private`, `.venv`, `.adk`, caches, and private exports out of GitHub.
Use the authenticated launcher; `adk web` is a developer interface outside this
security boundary. Revoke any previously exposed API key.
