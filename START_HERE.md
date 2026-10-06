# Start here — live Gemini version

The current app uses Google ADK and Gemini for every generated itinerary.
There is no offline mode. Open this project folder in VS Code; check that
`server.py`, `agent.py`, and `manage_users.py` appear in the sidebar.

## First-time setup

Choose **Terminal > New Terminal** and run these commands separately:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item travel_planner\.env.example travel_planner\.env
```

If you already have `.env`, skip the copy command to preserve your key.
Open `travel_planner/.env` in the editor and put your own key after
`GOOGLE_API_KEY=`. Keep `GOOGLE_GENAI_USE_VERTEXAI=FALSE`. Set your desired
compatible Gemini model after `TRAVEL_MODEL=` (default: `gemini-3.5-flash-lite`).
There should be no `TRAVEL_DEMO_MODE` line. Save with Ctrl+S.

Create your local app login if needed:

```powershell
.\.venv\Scripts\python.exe manage_users.py
```

Choose a lowercase username and a unique password of at least 12 characters.
Password typing is hidden. This app login is separate from Google/GitHub.
Existing accounts still work after upgrading; there is no default account.

## Start or restart

If an older server is running, stop it with Ctrl+C in its terminal.

```powershell
.\.venv\Scripts\python.exe server.py
```

Keep the terminal open. Visit **http://127.0.0.1:8001**, refresh the browser,
and sign in. The screen shows **Google ADK + Gemini** and your configured model.
The destination and hotel preference are text fields; the chat accepts natural
requests. Use the authenticated app rather than the ADK developer UI on port 8000.

## Try it

1. "I want to visit Jaipur for 3 days with a budget of ₹15,000. I like history and local food."
2. "Add a 4-star hotel and explain your choices. Update the estimated budget."
3. "Plan a trip to Kyoto and Osaka instead."
4. "Write a Python program." The response should redirect to itinerary planning.

Use **Save chat** to export your own examples. Keep keys/passwords out of screenshots.
The model gives estimates, not verified hotel availability or live prices.

## If something fails

- Page will not open: check the server is running and the address uses port 8001.
- Old form still appears: stop/restart the server from this folder and refresh.
- Missing Python/packages: finish the setup commands above.
- Missing API key: configure `.env` in the editor.
- API error: check the key, model access, and quota; wait before retrying.
- Port already in use: stop your earlier server with Ctrl+C.
- Account missing: run `manage_users.py` once to create it.

The GitHub link is for reviewing/downloading source. The localhost link opens
the app on the computer where the Python server is running.
