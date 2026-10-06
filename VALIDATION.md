# Validation — 6 October 2026

## Result

**83 automated tests passed** on Windows / Python 3.14.5.
The final browser JavaScript passed Node's syntax check.
The local browser was tested with a disposable offline-practice account:
sign-in, itinerary generation, budget display, and weather refusal worked.
Screenshots of that actual local interface are included and labeled offline.

## Important checks

| Check | Result |
|---|---|
| Two distinct accounts receive separate chats | Passed |
| Two browser logins to the same account start separate conversations | Passed |
| Unauthenticated history and planning calls | Rejected |
| Client-supplied user ID and session query parameters | Rejected |
| Missing or another session's CSRF token | Rejected |
| Foreign origin / foreign Host header | Rejected |
| Weather, office-distance, unrelated and known injection requests | Rejected before any provider call |
| Recognizable email, phone, key or passport content | Rejected; original message not retained |
| Invalid trip values, extra fields and oversized requests | Rejected |
| Real ADK Runner executes input/output callbacks | Passed using a local model double |
| Invalid model response / extra private output | Blocked |
| Output day count and catalog activity validation | Passed |
| Budget totals, group room count, reserve and low-budget handling | Passed |
| Session expiry, clear chat and revoked cookie reuse | Passed |
| Logout while generation is running | Late result discarded |
| Failed login and request rate limits | Passed |
| Provider failure | Generic error; no saved plan or provider payload |
| Developer, secret-file and unapproved static routes | Unavailable |

## Dependency check

`pip-audit` checked the 48 installed runtime packages listed in
`requirements-lock.txt` against its PyPI advisory service on the validation date.
**No known vulnerabilities were reported for those versions.** This is a known
advisory scan, not a guarantee that all dependencies are free of vulnerabilities.
The scan did not include the optional test tools. It can become outdated.

## Limits of this evidence

No authenticated live Gemini call was made for this upgraded build. ADK behavior
was tested with the actual installed ADK Runner and a deterministic local model
double. Offline screenshots do not demonstrate Gemini connectivity, output
quality, quota, or availability. Verify these with your own new API key.

This is an application test suite, not an independent penetration test or a
production security certification. Some SDK dependencies emitted deprecation
warnings (Python typing and Starlette's httpx test adapter); they did not fail
the tests. Review `SECURITY.md` before considering deployment outside loopback.
