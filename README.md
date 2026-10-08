# Personal Travel Planner

**[Instructions: setup, login, and usage](INSTRUCTIONS.md)** ·
**[How the code works](INSTRUCTIONS.md#how-the-code-works)** ·
**[Demo video folder](screenshots/)** ·
**[Example conversations](example_conversations.txt)** ·
**[Assignment 2 evaluation](#assignment-2-evaluation)**

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

## Assignment 2 evaluation

**Overall score: 69.27% across 12 live test cases.**
Six cases passed and six failed. Eight requests produced usable responses; four
returned an error. These are recorded results from 8 October 2026, not a promise
that later runs will give the same answers or scores. The submitted agent was
evaluated unchanged using `gemini-3.5-flash-lite`.

### Evaluation files

| File | Purpose |
|---|---|
| [agent.py](agent.py) | Existing Google ADK travel agent |
| [eval_dataset.json](eval_dataset.json) | 12 inputs and their expected behavior |
| [evaluator.py](evaluator.py) | Runs the real agent and the Gemini judge |
| [evaluation_results.json](evaluation_results.json) | Actual answers, observed tool calls, scores and reasons |
| [tests/test_evaluator.py](tests/test_evaluator.py) | Checks score calculation and incomplete results |

Keep these files with the existing `travel_planner/` package and dependencies.
Copying only `agent.py` and the evaluation files will not make a standalone app.

### Evaluation approach

1. Send each dataset input through the existing `Planner.reply` chat path. This
   runs the real ADK agent, input/output guardrails, response validation and
   budget formatting used by the app. No offline answers or model doubles are used.
2. Start each case with empty history. TC12 first creates its own Jaipur trip,
   then tests a hotel follow-up using only that case's history. ADK sessions are
   temporary and deleted by the engine. Existing user accounts/chats are not used.
3. Compare each actual displayed answer with that case's expected behavior.
   A separate Gemini call acts as the judge, using structured JSON scores.
   This implements the **LLM-as-a-Judge bonus**. The judge uses the same model
   by default; `TRAVEL_JUDGE_MODEL` can select a different compatible Gemini model.
4. Observe ADK function-call events. The agent currently has no tools. No call
   earns **1.0 for Tool Usage, marked not applicable**, rather than pretending
   the agent searched or booked anything. Model calls are not tool calls.
5. Review the saved answers against the rubric. The original Gemini assessments
   remain in `judge_assessment`. The review corrected a cost error the judge missed
   in TC11. Review notes and original scores are preserved alongside final scores.
6. Save results after each case. Judge failures remain pending until resumed.
   Never replace a failed answer with a successful retry to improve this report.

This evaluates agent responses, not the browser login or account isolation.
Those controls have separate automated tests. All evaluation inputs are synthetic
and safe to publish. No API key, password, login record or private chat is included.

### Metrics and scoring

| Metric | What it measures |
|---|---|
| Correctness | Correct destination, duration, preferences, budget and handling of invalid/missing information |
| Relevance | Focus on the requested trip or a suitable clarification/refusal |
| Completeness | All details required for that particular case |
| Tool Usage | Appropriate observed tool use, with no unsupported search/booking claims |

Scores range from **0 to 1**. The judge rubric uses 1 for fully met, 0.75 for
small gaps, 0.5 for substantial gaps, 0.25 for largely wrong and 0 for absent
or opposite behavior; intermediate scores are allowed. Asking for missing
information or declining a non-travel question can earn full marks.

`Case score = (Correctness + Relevance + Completeness + Tool Usage) / 4`

`Overall percentage = mean of all 12 case scores x 100`

A case passes when its mean is at least **0.80**, no required expected behavior
is missed, and no unexpected tool is called. This rule was chosen before scoring.
A high average alone does not hide a required behavior failure.
No usable response scores 0 for the three response metrics; Tool Usage still
scores 1 because no tool was available/needed/called. Errors are included in the
overall denominator. An incomplete run has no final overall score.

### Test cases and results

| Case | Test | Correctness | Relevance | Completeness | Tool Usage | Overall | Result |
|---|---|---:|---:|---:|---:|---:|---|
| TC01 | Valid 3-day Jaipur trip | 1.00 | 1.00 | 1.00 | 1.00 | 100.00% | Pass |
| TC02 | Valid 5-day Delhi trip | 1.00 | 1.00 | 1.00 | 1.00 | 100.00% | Pass |
| TC03 | Low-budget trip | 1.00 | 1.00 | 1.00 | 1.00 | 100.00% | Pass |
| TC04 | Missing destination | 0.25 | 0.50 | 0.25 | 1.00 | 50.00% | Fail |
| TC05 | Missing budget | 0.00 | 0.00 | 0.00 | 1.00 | 25.00% | Fail |
| TC06 | Invalid number of days | 0.00 | 0.00 | 0.00 | 1.00 | 25.00% | Fail |
| TC07 | Negative budget | 0.00 | 0.00 | 0.00 | 1.00 | 25.00% | Fail |
| TC08 | Historical-place preference | 0.00 | 0.00 | 0.00 | 1.00 | 25.00% | Fail |
| TC09 | Food preference | 1.00 | 1.00 | 1.00 | 1.00 | 100.00% | Pass |
| TC10 | Non-travel question | 1.00 | 1.00 | 1.00 | 1.00 | 100.00% | Pass |
| TC11 | International destination and currency | 0.50 | 1.00 | 0.75 | 1.00 | 81.25% | Fail |
| TC12 | Hotel follow-up | 1.00 | 1.00 | 1.00 | 1.00 | 100.00% | Pass |

Metric averages: Correctness **0.5625**,
Relevance **0.6250**,
Completeness **0.5833**,
Tool Usage **1.0000**.
Tool Usage is not applicable in every case, so its 1.0 increases the four-metric
average without proving any live search or booking ability.

### Failed cases and reasons

| Case | Observed failure | Suggested improvement |
|---|---|---|
| TC04 | Destination was missing; the agent chose Delhi and wrote a full plan instead of asking. | Make destination clarification explicit before generating an itinerary. |
| TC05 | Missing-budget request produced no usable response. | Improve safe error classification and structured-response handling; allow transparent budget assumptions or ask a concise question. |
| TC06 | Zero-day request produced no usable response instead of a useful correction. | Validate positive duration in chat as well as in the optional form. |
| TC07 | Negative-budget request produced no usable response instead of a useful correction. | Validate positive budgets in chat and return a clear correction request. |
| TC08 | Historical-preference request produced no usable response. | Check provider/quota and validation failures; use paced runs and bounded retries for transient errors. |
| TC11 | Food item was JPY 36000, but its assumption implies JPY 48000. The corrected trip total would be JPY 126000, above the cap. | Calculate quantities, rates, people and nights in Python; check every assumption against its amount. |

For TC05–TC08, the existing engine deliberately hides detailed exceptions.
This run cannot tell whether each failure came from the provider, quota, timeout
or response validation. A safe user-facing error is good for privacy, but the
evaluator needs safe error categories for diagnosis. Do not claim a confirmed
quota problem from these records alone.

Other improvements: leave a contingency for tight budgets; clarify hotel nights
from arrival/departure dates; remove instruction-like wording from hotel answers;
review judge scores because an LLM can miss arithmetic errors. A future search
tool could verify current facts and prices, but none is implemented here.

### Run the evaluation yourself

Use the same project setup and private `.env` as the app. An app login and a
running web server are not needed for this evaluator. From the project folder:

```powershell
.\.venv\Scripts\python.exe evaluator.py --output evaluation_results_new.json
```

This makes real Gemini calls and uses your API quota. Each accepted request uses
input check, itinerary generation and output review; the judge adds another call.
TC12 also has a setup request. Calls run one case at a time with a 10-second
pause between cases. The recorded initial run had no extra pause.

If a judge failed, keep its actual answer and resume:

```powershell
.\.venv\Scripts\python.exe evaluator.py --output evaluation_results_new.json --resume
```

`--resume` preserves scored cases, including failures. It only judges saved
pending answers. To perform a new full run, use a new output filename without
`--resume`. Results may differ because model responses and service availability
change. Review the JSON and update this README if submitting a later run.
The committed report includes an assisted review; a fresh run records raw judge
scores plus observed tool checks until you review it.

To verify scoring locally without API calls:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests\test_evaluator.py
```

References: [ADK evaluation](https://adk.dev/evaluate/) and
[Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output).

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
| Running evidence | [Demo video](https://github.com/shivangmohanty-stack/personal-travel-planner-agent/blob/main/screenshots/Example%20video%20Shivang%20Mohanty.mp4) |
| Three example conversations | `example_conversations.txt` |

Supporting files: `server.py` (local API), `security.py` (login/session controls),
`manage_users.py` (account setup), `travel_planner/guardrails.py` (schemas/checks),
`travel_planner/engine.py` (ADK requests/budget arithmetic), and `static/` (browser).
`travel_planner/agent.py` imports the root agent for ADK package discovery.

The previous screenshots have been removed. The owner's [demo video](https://github.com/shivangmohanty-stack/personal-travel-planner-agent/blob/main/screenshots/Example%20video%20Shivang%20Mohanty.mp4)
is now available in the GitHub `screenshots/` folder. This evaluation does not
change that recording. See
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
