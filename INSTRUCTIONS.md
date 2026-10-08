# Instructions

[Setup](#first-time-setup-on-windows) · [Create a login](#create-your-app-login) ·
[Start](#start-the-planner) · [Use the app](#use-the-planner) ·
[Code guide](#how-the-code-works) · [Add a video](#add-your-demo-video) ·
[Troubleshooting](#troubleshooting)

A reviewer can use this guide to set up and understand the project from the
repository. GitHub stores the code; the website runs locally on the computer
that starts the Python server. Live Gemini requires an internet connection
and the reviewer's own API key. There is no shared login or offline planner.

## First-time setup on Windows

### 1. Download and open the project

1. On the repository page, choose **Code → Download ZIP** and extract it.
2. In VS Code, choose **File → Open Folder**. Select the extracted folder
   containing `agent.py`, `server.py`, and `requirements.txt`.
3. Choose **Terminal → New Terminal**. Use PowerShell for the commands below.

Python 3.11 or newer is recommended; this project was tested with Python 3.14.
Check your installation:

```powershell
python --version
```

If Python is missing, install it from [python.org](https://www.python.org/downloads/),
enable its PATH option, and reopen VS Code.

### 2. Install the packages

Run each command separately in the project terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Wait until installation finishes and the terminal prompt returns. Using the
environment's Python directly means you do not need an activation command.

### 3. Configure Gemini

Create the local settings file once:

```powershell
Copy-Item travel_planner\.env.example travel_planner\.env
```

**Skip the copy command if `.env` already contains your settings.** Open
[Google AI Studio's API keys page](https://aistudio.google.com/api-keys), sign in
with your Google account, and create or select your own Gemini API key. Follow
any project setup prompts. Google's [API key guide](https://ai.google.dev/gemini-api/docs/api-key)
explains the setup.

In VS Code, expand `travel_planner` and open `.env`. Replace the key placeholder
with your own key and save with **Ctrl+S**:

```text
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=PASTE_YOUR_GEMINI_API_KEY_HERE
TRAVEL_MODEL=gemini-3.5-flash-lite
```

These lines belong in the **`.env` file**, not as commands in PowerShell.
The placeholder must be replaced before generating an itinerary.
`TRAVEL_MODEL` selects a compatible Gemini model; restart the server after changing
it. This implementation connects to Gemini. Keep `.env` local; only the template
`.env.example` belongs in the repository.

## Create your app login

This login is separate from your Google and GitHub accounts. There is no default
username or password. Run this command once for each new account:

```powershell
.\.venv\Scripts\python.exe manage_users.py
```

1. Enter a username with **3–32 lowercase letters, numbers, or underscores**.
2. Enter a unique password with **12–128 characters**, then press Enter.
3. Repeat the same password when asked.
4. Wait for **Account created**.

Password typing shows no characters or dots; this is normal. Password hashes
are saved locally in `.private/users.json`. Do not upload that folder.
If you already created an account on this computer, use it again.
Each login session has its own temporary conversation.

## Start the planner

From the project terminal, run:

```powershell
.\.venv\Scripts\python.exe server.py
```

Keep the terminal open. Visit **http://127.0.0.1:8001** in your browser and sign in
with your app account. The page should show **Google ADK + Gemini** and the model
name. After initial setup, you can also double-click **`start.cmd`** in the folder.

Press **Ctrl+C** in the terminal to stop the server. To restart, run the server
command again and refresh the browser. Use this authenticated app for the demo;
the ADK developer interface is outside its login boundary. A localhost link works
only on the computer running the server; GitHub does not host the live app.

## Use the planner

Enter this in **Tell me about your trip**, then press **Send**:

> I want to visit Jaipur for 3 days with a budget of ₹15,000. I like history and local food.

Wait for the reply. It should include a day-wise itinerary, places to visit,
food, accommodation suggestions, local transport, and an estimated budget.
The **Build your trip** form is an optional way to enter the same preferences.

Continue naturally:

> Add a 4-star hotel and update the estimated budget. Explain your choices.

> Make the itinerary more relaxed and include vegetarian food.

Different destinations, durations, currencies, and group sizes are supported;
there is no fixed city or price catalog. The agent asks questions when important
details are missing. An unrelated request, such as a programming task, should
receive a polite redirect to itinerary planning.

| Control | What it does |
|---|---|
| Send | Sends a trip request or follow-up to the live planner. |
| Create my itinerary | Sends the preferences from the optional form. |
| Save chat | Downloads this login's conversation as a text file. |
| Clear chat | Removes this session's chat and resets the trip form. |
| Sign out | Ends this login session and clears its temporary chat. |

Chats are temporary and expire. Save your examples before signing out if needed;
exports remain ordinary files on your computer. Accepted trip messages and recent
travel context are sent to Gemini. Prices, hotel ratings, and availability need
checking before booking.

## How the code works

Start with [agent.py](agent.py), then follow these files:

| File | Responsibility |
|---|---|
| [agent.py](agent.py) | Configures Gemini and the ADK input/output scope callbacks. |
| [travel_planner/guardrails.py](travel_planner/guardrails.py) | Defines request/response formats and local checks for recognizable secrets and instruction attacks. |
| [travel_planner/engine.py](travel_planner/engine.py) | Runs temporary ADK sessions and sums the model's budget estimates in Python. |
| [server.py](server.py) | Serves the app, authenticates requests, and supplies only this login's accepted chat context. |
| [security.py](security.py) | Handles password hashes, cookies, expiry, and request limits. |
| [manage_users.py](manage_users.py) | Creates an app account locally. |
| [static/index.html](static/index.html), [static/app.js](static/app.js), [static/style.css](static/style.css) | Build the page, send requests, and display replies safely as text. |
| [requirements.txt](requirements.txt) | Lists the packages needed to run the app. |
| [tests/](tests/) | Checks guardrails, account isolation, request handling, and budget arithmetic. |

A message follows this route:

1. The browser sends it to the authenticated local server.
2. The server checks the login, request boundaries, and recognizable private input.
3. A Gemini scope check decides whether it belongs to itinerary planning.
4. The ADK agent responds using this login's recent accepted travel context.
5. The response format, recognizable secrets, and travel scope are reviewed.
6. Python adds the estimated cost items; the browser displays the reviewed reply.

Login isolation is enforced by server code. Model guardrails are best-effort and
do not guarantee that every attack or personal detail will be detected.
The agent has no tools for reading files, running commands, or booking trips.
See [SECURITY.md](SECURITY.md) for the privacy boundary and
[VALIDATION.md](VALIDATION.md) for the recorded checks.

To run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The [three example conversations](example_conversations.txt) were recorded using
live Gemini with synthetic requests. Model doubles appear only in automated tests.

## Add your demo video

The previous screenshot files have been removed. GitHub cannot retain an empty
directory, so [screenshots/](screenshots/) was initially created with an empty `.gitkeep` file
to keep the folder available. The placeholder is not demo evidence.

1. Record the app: sign in, request an itinerary, revise the hotel preference,
   and show an unrelated-topic refusal. Keep passwords, API keys, and private
   information out of the recording.
2. Save the recording as **`demo.mp4`**.
3. Open the repository's **screenshots** folder on GitHub.
4. Choose **Add file** (or **⋯**) → **Upload files**.
5. Drag the video onto that upload page, wait for it to upload, and click
   **Commit changes** to save it to this repository.

Keep a browser-uploaded video under **25 MiB**, GitHub's per-file browser upload
limit. See [GitHub's upload instructions](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).
Shorten or compress the recording if necessary. The owner's [demo video](https://github.com/shivangmohanty-stack/personal-travel-planner-agent/blob/main/screenshots/Example%20video%20Shivang%20Mohanty.mp4) is now in the repository.
After uploading, a reviewer can open `screenshots/demo.mp4` from the repository.

## Troubleshooting

| What you see | What to do |
|---|---|
| Python is not recognized | Install Python, enable PATH, and reopen VS Code. |
| Cannot find a file | Open the folder containing `server.py`; run commands from its terminal. |
| Missing packages | Run the requirements installation command and wait for completion. |
| No account / invalid login | Create an account with `manage_users.py`; use its exact username and password. |
| Password looks blank in the terminal | Continue typing and press Enter; password input is hidden. |
| Missing API key | Edit `travel_planner/.env`, replace the placeholder, save, and restart. |
| Gemini cannot complete the request | Check the key, model access, and quota; wait before retrying. There is no offline fallback. |
| Browser cannot open the page | Keep the server running and use `http://127.0.0.1:8001`. |
| Port already in use / old page | Stop the earlier planner server with Ctrl+C, restart from this project, and refresh. |
| Signed out after inactivity | Sign in again; expired temporary chats are cleared. |

Keep `.env`, `.private`, `.venv`, and private chat exports out of GitHub.

## Run Assignment 2 evaluation

The evaluator tests the existing live agent without starting the website or
signing in. Configure your private Gemini `.env` first, then run:

```powershell
.\.venv\Scripts\python.exe evaluator.py --output evaluation_results_new.json
```

It saves the actual answers and scores in JSON. This uses Gemini API quota.
Read [the evaluation report](README.md#assignment-2-evaluation) for the dataset,
metrics, results, failures and resume instructions. The committed report is a
recorded run; a new run may score differently.
