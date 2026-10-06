# Start here

This project runs on your computer. GitHub stores the source files; it does not
automatically host the Python app. The app link works while `server.py` is running.

## 1. Open the correct folder

Use this folder, not your earlier `TravelPlannerAgent` folder.
In VS Code choose **File > Open Folder** and select `personal-travel-planner-agent`.
Check that `agent.py`, `server.py`, `manage_users.py`, and `requirements.txt` are
visible in the left sidebar. Choose **Terminal > New Terminal**.

## 2. Install once

Run these commands separately:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item travel_planner\.env.example travel_planner\.env
```

Do not paste the contents of `.env` into the terminal.

## 3. First try the interface without an API key

Open `travel_planner/.env` in the VS Code editor. Change its last line to:

```text
TRAVEL_DEMO_MODE=TRUE
```

Save with Ctrl+S. This is the same offline practice mode used in the included
preview screenshots. It proves the interface and guardrails run without needing
Google quota. It is not a live Gemini run.

## 4. Create your app sign-in

In the terminal run:

```powershell
.\.venv\Scripts\python.exe manage_users.py
```

Choose your own lowercase username, for example `student`.
Choose a unique password of at least 12 characters and repeat it when asked.
Typing a password shows no characters. Press Enter after typing each password.
Wait for **Account created**.

This creates the login for this local travel app. It is separate from your
Google/GitHub accounts. No default login or the assistant's test account is included.

## 5. Start and open the app

```powershell
.\.venv\Scripts\python.exe server.py
```

Wait for **Travel Planner: http://127.0.0.1:8001**. Keep this terminal open.
Open that address in your browser. Sign in using the account you just created.
Use the trip form to create a Jaipur plan, then test weather and office queries.

For later runs, you can double-click `start.cmd` in this folder.

## 6. Switch to the actual Gemini agent

Stop the server with Ctrl+C. Open `travel_planner/.env` in the editor.
Paste your own new Gemini API key after `GOOGLE_API_KEY=` and set:

```text
TRAVEL_DEMO_MODE=FALSE
```

Save, then start the server again. The screen should say **Google ADK + Gemini**.
Capture that screen and the real itinerary for your assignment.

## If the page does not open

- Check that the server terminal is still open and shows the app address.
- Use port **8001** for this version, not the old ADK page on port 8000.
- If the terminal says the port is in use, stop another copy with Ctrl+C.
- If it says create an account first, complete step 4.
- If it says add an API key, either configure your key or use step 3 to try offline.
- If the screen gives a Gemini error, the interface is running but generation
  failed. Check your key/model/quota or wait and retry. Offline mode remains
  available for testing the security controls.

## Your mentor's required deliverables

| Required item | Location |
|---|---|
| Agent code | `agent.py` at the root |
| Dependencies | `requirements.txt` |
| Project documentation | `README.md` |
| Screenshot/video | `screenshots/` — replace/add your live Gemini evidence |
| Three example conversations | `example_conversations.txt` — included offline examples are labeled |

Keep supporting modules and the browser files too: they implement security and
the interface. Do not upload `.env`, `.private`, `.venv`, or private chat exports.
