"""Authenticated local app. Never expose ADK's developer API as a private service."""

import asyncio
import hmac
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from security import COOKIE, USER_FILE, RateLimiter, SessionStore, verify_user
from travel_planner.catalog import INTERESTS, PLACES
from travel_planner.engine import Planner, PlanningUnavailable
from travel_planner.guardrails import TripSpec, parse_message
from travel_planner.planning import estimate_budget, render_plan

BASE = Path(__file__).resolve().parent
ORIGINS = {"http://127.0.0.1:8001", "http://localhost:8001"}
HOSTS = {"127.0.0.1:8001", "localhost:8001"}
SECURITY_HEADERS = {
    "cache-control": "no-store",
    "content-security-policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "permissions-policy": "geolocation=(), camera=(), microphone=()",
    "cross-origin-resource-policy": "same-origin",
}


class RequestBoundary:
    """Bound bytes before JSON parsing and reject foreign origins/Host headers."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def safe_send(message):
            if message["type"] == "http.response.start":
                message["headers"] += [(key.encode(), value.encode()) for key, value in SECURITY_HEADERS.items()]
            await send(message)

        async def reject(code, text):
            await JSONResponse({"detail": text}, status_code=code)(scope, receive, safe_send)

        headers = {}
        for key, value in scope["headers"]:
            key = key.lower()
            if key in headers and key in {b"host", b"origin", b"content-length", b"content-type"}:
                await reject(400, "Invalid request headers.")
                return
            headers[key] = value.decode("latin-1")
        if headers.get(b"host") not in HOSTS:
            await reject(400, "This app only accepts its local address.")
            return
        if scope.get("query_string") and scope["path"].startswith("/api/"):
            await reject(400, "Client-supplied user/session identifiers are not accepted.")
            return
        mutation = scope["method"] not in {"GET", "HEAD"}
        if mutation:
            if headers.get(b"origin") not in ORIGINS or headers[b"origin"] != "http://" + headers[b"host"]:
                await reject(403, "Use the travel app from its local browser page.")
                return
            if headers.get(b"content-type", "").split(";")[0].strip() != "application/json":
                await reject(415, "JSON requests only.")
                return
        if b"origin" in headers and headers[b"origin"] not in ORIGINS:
            await reject(403, "Cross-origin access is disabled.")
            return
        if headers.get(b"sec-fetch-site") == "cross-site":
            await reject(403, "Cross-site access is disabled.")
            return
        try:
            length = int(headers.get(b"content-length", "0"))
        except ValueError:
            await reject(400, "Invalid request size.")
            return
        if length < 0 or length > 8192:
            await reject(413, "Request is too large.")
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 8192:
                await reject(413, "Request is too large.")
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, safe_send)


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(pattern=r"^[a-z0-9_]{3,32}$")
    password: str = Field(min_length=1, max_length=128)


class ChatBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1000)


def create_app(planner=None, users_path=USER_FILE, store=None):
    @asynccontextmanager
    async def lifespan(app):
        async def sweep_expired_chats():
            while True:
                await asyncio.sleep(30)
                app.state.store.prune()
        task = asyncio.create_task(sweep_expired_chats())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            for session in app.state.store.sessions.values():
                session.revoked = True
                session.messages.clear()
                session.trip = None
            app.state.store.sessions.clear()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(RequestBoundary)
    app.state.store = store or SessionStore()
    app.state.limiter = RateLimiter()
    app.state.planner = planner or Planner()
    app.state.model_slots = asyncio.Semaphore(3)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # FastAPI's default includes submitted values; never echo them.
        return JSONResponse({"detail": "Invalid fields. Use the trip form and listed limits."}, status_code=422)

    @app.exception_handler(Exception)
    async def internal_error(request, error):
        return JSONResponse({"detail": "The request could not be completed. Try again."},
                            status_code=500, headers=SECURITY_HEADERS)

    @app.middleware("http")
    async def api_rate_limit(request, call_next):
        if request.url.path.startswith("/api/"):
            peer = request.client.host if request.client else "local"
            if not app.state.limiter.allow(("requests", peer), 120, 60):
                return JSONResponse({"detail": "Too many requests. Wait a minute."}, status_code=429,
                                    headers={**SECURITY_HEADERS, "Retry-After": "60"})
        return await call_next(request)

    def authenticated(request, write=False):
        session = app.state.store.get(request.cookies.get(COOKIE))
        if session is None:
            raise HTTPException(401, "Please sign in again.")
        if write and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
            raise HTTPException(403, "Request verification failed. Reload the page.")
        return session

    @app.get("/")
    async def home():
        return FileResponse(BASE / "static" / "index.html")

    @app.get("/static/{filename}")
    async def static_file(filename: str):
        if filename not in {"app.js", "style.css"}:
            raise HTTPException(404, "Not found.")
        return FileResponse(BASE / "static" / filename)

    @app.post("/api/login")
    async def login(body: LoginBody, request: Request):
        peer = request.client.host if request.client else "local"
        allowed_peer = app.state.limiter.allow(("login_ip", peer), 10, 60)
        allowed_name = app.state.limiter.allow(("login_user", body.username), 5, 60)
        if not allowed_peer or not allowed_name:
            raise HTTPException(429, "Too many sign-in attempts. Wait a minute.")
        user_id = await run_in_threadpool(verify_user, body.username, body.password, users_path)
        if not user_id:
            raise HTTPException(401, "Username or password is incorrect.")
        app.state.store.revoke(request.cookies.get(COOKIE))
        try:
            token = app.state.store.create(user_id)
        except ValueError:
            raise HTTPException(503, "The app is at capacity. Try again later.") from None
        response = JSONResponse({"ok": True})
        # HTTP is permitted ONLY on loopback. Production requires HTTPS + Secure.
        response.set_cookie(COOKIE, token, httponly=True, samesite="strict",
                            secure=False, max_age=1800, path="/")
        return response

    @app.get("/api/me")
    async def me(request: Request):
        session = authenticated(request)
        return dict(csrf=session.csrf, demo=bool(app.state.planner.demo),
                    destinations=list(PLACES), interests=list(INTERESTS),
                    expires_in=max(0, int(1800 - (app.state.store.clock() - session.created))))

    @app.get("/api/history")
    async def history(request: Request):
        session = authenticated(request)
        async with session.lock:
            if session.revoked:
                raise HTTPException(401, "Please sign in again.")
            return dict(messages=list(session.messages), trip=session.trip.model_dump() if session.trip else None)

    @app.post("/api/logout")
    async def logout(request: Request):
        session = authenticated(request, write=True)
        # Mark revoked immediately so an in-flight result cannot recreate history.
        app.state.store.revoke(request.cookies.get(COOKIE))
        response = JSONResponse({"ok": True})
        response.delete_cookie(COOKIE, path="/")
        return response

    @app.post("/api/clear")
    async def clear(request: Request):
        session = authenticated(request, write=True)
        async with session.lock:
            if session.revoked:
                raise HTTPException(401, "Please sign in again.")
            session.trip = None
            session.messages.clear()
        return dict(ok=True)

    async def process(trip, reply, session):
        if reply:
            session.messages.append(dict(role="assistant", text=reply))
            session.messages[:] = session.messages[-24:]
            return dict(messages=list(session.messages), trip=session.trip.model_dump() if session.trip else None)
        budget = estimate_budget(trip)
        if not budget["feasible"]:
            text = (f"This trip needs an estimated ₹{budget['total']:,} including reserve, "
                    f"which is ₹{-budget['remaining']:,} over your budget. "
                    "Try fewer days, fewer travelers, economy accommodation, or a larger budget.")
            session.messages.append(dict(role="assistant", text=text))
            session.messages[:] = session.messages[-24:]
            return dict(messages=list(session.messages), trip=session.trip.model_dump() if session.trip else None)
        if not app.state.limiter.allow(("model", session.user_id), 30, 3600):
            raise HTTPException(429, "Planning limit reached. Try again in an hour.")
        try:
            await asyncio.wait_for(app.state.model_slots.acquire(), timeout=2)
        except TimeoutError:
            raise HTTPException(503, "The planner is busy. Try again shortly.") from None
        try:
            async with asyncio.timeout(50):
                choice, source = await app.state.planner.choose(trip, session.user_id)
                plan = render_plan(trip, choice, source)
        except (PlanningUnavailable, TimeoutError, ValueError):
            raise HTTPException(503, "Gemini is unavailable or its answer failed validation. Wait and try again. No plan was saved.") from None
        finally:
            app.state.model_slots.release()
        app.state.store.prune()
        if session.revoked:
            raise HTTPException(401, "Your session ended. Please sign in again.")
        session.trip = trip
        summary = (f"{trip.destination} · {trip.days} days · ₹{trip.budget:,} total · "
                   f"{trip.travelers} traveler(s) · {', '.join(trip.interests)} · {trip.stay}")
        session.messages.extend([dict(role="user", text=summary), dict(role="assistant", plan=plan)])
        session.messages[:] = session.messages[-24:]
        return dict(messages=list(session.messages), trip=trip.model_dump())

    async def writable_session(request):
        session = authenticated(request, write=True)
        if not app.state.limiter.allow(("chat", session.user_id), 10, 60):
            raise HTTPException(429, "Too many messages. Wait a minute.")
        return session

    @app.post("/api/plan")
    async def plan(body: TripSpec, request: Request):
        session = await writable_session(request)
        async with session.lock:
            if session.revoked:
                raise HTTPException(401, "Please sign in again.")
            return await process(body, None, session)

    @app.post("/api/chat")
    async def chat(body: ChatBody, request: Request):
        session = await writable_session(request)
        async with session.lock:
            if session.revoked:
                raise HTTPException(401, "Please sign in again.")
            trip, reply = parse_message(body.message, session.trip)
            return await process(trip, reply, session)

    return app


if __name__ == "__main__":
    import os
    import uvicorn
    from dotenv import load_dotenv
    from security import read_users

    load_dotenv(BASE / "travel_planner" / ".env", override=False)
    demo = os.getenv("TRAVEL_DEMO_MODE", "FALSE").upper() == "TRUE"
    if not read_users():
        raise SystemExit("Create an account first: .venv\\Scripts\\python.exe manage_users.py")
    if not demo and not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit("Add GOOGLE_API_KEY to travel_planner/.env first. Keep the key private.")
    # Suppress SDK/application payload logs. The launcher does not install tracing.
    logging.disable(logging.CRITICAL)
    print("Travel Planner: http://127.0.0.1:8001")
    print("Offline practice mode." if demo else "Gemini mode. Only validated trip fields are sent to Google.")
    uvicorn.run(create_app(Planner(demo=demo)), host="127.0.0.1", port=8001,
                access_log=False, log_level="critical", server_header=False)
