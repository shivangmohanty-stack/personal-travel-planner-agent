# Security boundary

## What the app protects

The supported launcher binds to `127.0.0.1:8001`. Separate accounts and opaque
browser cookies prevent an ordinary user from retrieving another login's chat
through the supported API. The server chooses the account identity; the browser
cannot provide a user ID or session ID. There is no chat-list or debug endpoint.

Password hashes use scrypt (N=32768, r=8, p=3) with a unique 16-byte salt.
Passwords are never stored in plaintext. Login cookies use 256-bit random tokens,
HttpOnly, SameSite=Strict, and a 30-minute maximum age. Only their SHA-256 digests
are held server-side. Mutations require the matching session's CSRF token and
same local origin. An expired cookie cannot read data even if a page is still open.

Session history is memory-only, at most 24 messages per login. Inactive sessions
expire after 15 minutes; absolute expiry is 30 minutes. Expired data is swept on
requests and every 30 seconds. Sign-out revokes the cookie and removes the chat.
Each ADK generation uses a fresh session which is deleted afterwards. Clear-chat
waits for an active generation, then discards the completed history and trip.

## How scope and data minimization work

The chat grammar is an allowlist of documented trip requests and revisions.
Weather, distance, office queries, unrelated wording, known injection phrases,
links, and recognizable secret/contact patterns are rejected locally. The API
also accepts a form with enumerated cities/interests, bounded integers, and no
extra fields. No original user message or username is included in a model request.

Gemini receives only validated trip fields and the selected city's catalog.
Its allowed response is day numbers and activity IDs. The app verifies the exact
day count, order, IDs, duplicate stops, requested food, and daytime historical
visits. Extra fields and invalid answers fail closed. Visible itinerary words
come from code/catalog, not arbitrary model prose. Budgets are calculated in
Python. The browser inserts text using `textContent`, never `innerHTML`.

The agent has no file, shell, browser, retrieval, booking, or account tools.
The supported launcher suppresses SDK payload logs and does not configure tracing
or an external telemetry exporter. Structured output and callbacks complement
the prompt; they do not rely on a prompt alone for access control.

## Resource limits

- 8192 request bytes, checked before JSON parsing; 1000 chat characters.
- At most 100 active browser sessions; 24 messages each.
- 120 API requests per client/minute; 10 sign-in attempts per client/minute
  and 5 per username/minute.
- 10 chat/form requests per account/minute; 30 planning attempts/hour.
- Three concurrent generations; bounded wait, call count, retries, and timeout.
- Provider errors and invalid responses do not create a saved itinerary.

## What this cannot protect against

- Someone controlling the computer, OS account, browser profile, or process memory.
- Someone using an unlocked signed-in browser or stealing an active cookie.
- Private exported files, screenshots, browser history, OS backups, or Google-side
  processing/retention. No secure deletion from RAM, swap, or backups is claimed.
- A full DLP detector: input regexes are heuristic. Safety comes chiefly from
  accepting only bounded fields and never forwarding arbitrary user text.
- Accurate live opening times, prices, weather, or routing. The small catalog
  and sample costs are educational assumptions.
- Distributed rate limiting, internet deployment, or a multi-process server.

On Windows, `.private` and `.env` inherit the folder's OS permissions; Python's
Unix file mode does not create Windows ACLs. Keep them in your private user folder.
HTTP cookies intentionally lack `Secure` on this loopback-only app. An internet
deployment needs HTTPS, Secure cookies, managed authentication, least-privilege
secret storage, shared session/rate-limit storage, privacy review, and security
testing before exposure. Do not change the host to `0.0.0.0` for this prototype.

Use `server.py`, not `adk web`, for private chat. Developer tooling can expose
raw events and is outside this boundary. Keep keys out of screenshots and ZIPs;
revoke any key already exposed.
