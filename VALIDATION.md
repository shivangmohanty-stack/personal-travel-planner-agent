# Validation — live Gemini upgrade

Date: 6 October 2026. Python 3.14 / google-adk 2.11.0 / google-genai 2.28.0.

## Automated checks

54 tests passed. These exercise real ADK Runner callbacks using model doubles,
portable Gemini response schemas, unrestricted destinations, hotel follow-ups,
variable budget arithmetic, private input checks, output review, two-account and
separate-login isolation, CSRF, origin/Host validation, expiry, logout during a
generation, error handling, and rate limits. SDK deprecation warnings were present.
The model doubles are test fixtures only; the app has no offline planner.

## Real Gemini checks

The configured `gemini-3.5-flash-lite` model was called using a locally configured
key that is not included in the repository. Synthetic requests tested:

- Jaipur: three days, INR 15,000, history and food — detailed itinerary returned.
- Follow-up: add a 4-star hotel, retain original budget, explain tradeoffs — answered.
- Kyoto and Osaka: ten days, two adults, JPY budget — itinerary returned.
- Paris: four days, family of three, vegetarian food, EUR budget — itinerary returned.
- Standalone weather, office commute, and programming requests — refused.

The tests used independent temporary sessions and synthetic travel requests,
not anyone's existing chat. Source schemas were adapted to portable Gemini wire
fields; strict local response validation remains in place.

## Evidence and limits

`example_conversations.txt` contains the recorded live synthetic conversations.
The live validation used a disposable test account on loopback port 8003;
the normal launcher uses 8001. The earlier validation screenshots were removed
at the project owner's request to leave `screenshots/` ready for their own
demo video. No video has been uploaded yet. No key, password, account store,
or private export is submitted.

Scope classification is model-dependent and can make mistakes. These checks do
not prove every jailbreak will be stopped or every personal detail will be
detected. Server-enforced account isolation is independent of the model.
Hotel ratings, rates, opening times, and availability were not live-verified.
Generated budgets are estimates, summed in Python; no purchases or bookings occur.
