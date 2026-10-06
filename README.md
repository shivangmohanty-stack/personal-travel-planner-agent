# Personal Travel Planner

**[Instructions: setup, login, and usage](INSTRUCTIONS.md)** ·
**[How the code works](INSTRUCTIONS.md#how-the-code-works)** ·
**[Demo video folder](screenshots/)** ·
**[Example conversations](example_conversations.txt)**

A simple **live Google ADK + Gemini** agent that creates and revises travel
itineraries. Describe your trip naturally, or use the optional form. There is no
offline planner, destination allowlist, fixed attraction catalog, or preset price
table. Gemini recommends activities and explains the plan for your request.

Examples of supported requests:

- "I want to visit Jaipur for 3 days with a budget of ₹15,000. I like history and local food."
- "Add a 4-star hotel, explain the choices, and update the budget."
- "Plan 10 days in Kyoto and Osaka for two adults, with a relaxed pace."
- "Make it cheaper", "Why did you choose that place?", or "Include vegetarian food."

The planner helps with day-wise schedules, destinations, accommodation,
attractions, food, travel logistics, accessibility, and estimated budgets.
It asks questions when essential information is missing. Hotel prices, official
star ratings, opening times, and availability are **not live-verified**: confirm
them before booking. There is no booking or live search tool.

## Start on Windows

Follow [START_HERE.md](START_HERE.md). Python 3.11+ is recommended; this version
was tested using Python 3.14. Open this project folder in VS Code and run each
command separately in its terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item travel_planner\.env.example travel_planner\.env
```

Skip the copy command if `.env` already contains your key. Edit `.env` in the
editor, not the terminal. Set your own Gemini API key and model:

```text
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_PRIVATE_KEY
TRAVEL_MODEL=gemini-3.5-flash-lite
```

Any compatible Gemini text model supporting structured responses can be selected
using `TRAVEL_MODEL`. Restart the server after changing it. This project currently
uses the Gemini provider; other providers need an ADK model adapter and credentials.
There is no `TRAVEL_DEMO_MODE` setting anymore.

Create your local app login if you have not already done so, then start:

```powershell
.\.venv\Scripts\python.exe manage_users.py
.\.venv\Scripts\python.exe server.py
```

Choose a lowercase username and a unique password with at least 12 characters.
Typing a password shows nothing; press Enter when finished. Open
**http://127.0.0.1:8001**, sign in, and describe your trip. Keep the terminal open.
For subsequent starts, double-click `start.cmd`. GitHub hosts the source files;
it does not run this Python app.

## Guardrails without restricting destinations

1. Small local checks reject recognizable secrets and obvious instruction attacks.
2. A short Gemini intent check determines whether the request belongs to itinerary
   planning, including hotel requests and contextual follow-up questions.
3. The Google ADK agent creates a detailed response using only this login's recent
   accepted travel conversation.
4. The app validates the response and reviews its scope before displaying it.
   Estimated cost items come from Gemini; Python calculates the total and balance.

An unrelated request receives:

> I can help create and improve travel itineraries, including places to visit,
> accommodation, food, transport, and estimated budgets. Please keep your request
> related to planning a trip.

Trip-related climate considerations or transport distances may be useful for an
itinerary. Standalone forecasts and everyday office commutes remain outside scope.
No list of cities or exact chat phrases is used. Message length, request limits,
and positive numeric values are resource/validation boundaries, not city limits.

Accepted messages and recent travel history are sent to Google Gemini. Even an
unrelated message may reach the intent checker; obvious detected secrets are
stopped locally. Three small/bounded model stages are used for an accepted request:
input check, itinerary response, output review. There is no automatic offline
fallback or automatic switch to another model. Provider errors show a generic retry
message, with no new answer saved.

## Privacy and login

- Salted password hashes; opaque HttpOnly, SameSite cookies; CSRF/origin checks.
- Each login has its own temporary chat. The browser cannot choose another user ID.
- Chats stay in memory, limited to the most recent 24 messages. The model receives
  at most 12 accepted messages from that login. ADK request sessions are deleted.
- Clear chat, sign-out, expiry (15 minutes idle / 30 minutes absolute), and server
  restart remove the corresponding in-app history.
- Account hashes stay in `.private/users.json`; your key stays in `.env`.
- No file/shell/account tools, public chat endpoints, HTML injection, or app tracing.
- The launcher binds only to your local computer. See [SECURITY.md](SECURITY.md).

This is a local learning project. Model scope checks and secret detection are
best-effort protections, not a promise that every attack or every private detail
can be detected. Account isolation is enforced by server code, not by asking the
model to protect it. Anyone using an unlocked signed-in browser can see that chat.

## Assignment files

| Required item | File |
|---|---|
| Google ADK agent | `agent.py` |
| Dependencies | `requirements.txt` |
| Setup, login, and usage | [INSTRUCTIONS.md](INSTRUCTIONS.md) |
| Running evidence | [screenshots/](screenshots/) — ready for the owner's demo video |
| Three example conversations | `example_conversations.txt` |

Supporting files: `server.py` (local API), `security.py` (login/session controls),
`manage_users.py` (account setup), `travel_planner/guardrails.py` (schemas/checks),
`travel_planner/engine.py` (ADK requests/budget arithmetic), and `static/` (browser).
`travel_planner/agent.py` imports the root agent for ADK package discovery.

The previous screenshots have been removed. The `screenshots/` folder contains
only an empty `.gitkeep` placeholder so GitHub can retain it. Upload your own
video there as `demo.mp4`; no demo video is included yet. See
[video upload instructions](INSTRUCTIONS.md#add-your-demo-video).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Automated model doubles test the actual ADK callbacks without spending API quota;
they are test fixtures, not an offline app mode. See [VALIDATION.md](VALIDATION.md)
for live checks, automated checks, and evidence limits.

Keep `.env`, `.private`, `.venv`, caches, and private exports out of GitHub.
Prepared with AI assistance; read, test, and adapt the code for your internship.

## Instructor reference

The [Google Docs ADK codelab](https://codelabs.developers.google.com/google-docs-adk-agent)
informed the ADK structure/configuration/local testing. This project does not need
Google Docs permissions, Cloud deployment, or a service account.
References: [ADK callbacks](https://adk.dev/callbacks/types-of-callbacks/),
[Gemini models](https://ai.google.dev/gemini-api/docs/models), and
[Gemini API key setup](https://ai.google.dev/gemini-api/docs/api-key).
