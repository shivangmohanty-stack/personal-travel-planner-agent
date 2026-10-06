"""A fresh in-memory ADK conversation for each normalized planning request."""

import asyncio
import os
import uuid

from .guardrails import PlanChoice
from .planning import demo_choices, validate_choices


class PlanningUnavailable(Exception):
    """The only provider error exposed to the application."""


class Planner:
    def __init__(self, demo=False):
        self.demo = demo
        self._runner = None
        self._sessions = None

    def _initialize(self):
        if self._runner is not None:
            return
        if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() not in {"FALSE", "0"}:
            raise PlanningUnavailable()
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from .agent import root_agent

        self._sessions = InMemorySessionService()
        self._runner = Runner(agent=root_agent, app_name="private_travel_planner",
                              session_service=self._sessions)

    async def choose(self, trip, user_id):
        if self.demo:
            return demo_choices(trip), "Offline practice — catalog planner"
        session_id = uuid.uuid4().hex
        try:
            self._initialize()
            from google.genai import types
            from google.adk.agents.run_config import RunConfig
            await self._sessions.create_session(app_name="private_travel_planner",
                                                user_id=user_id, session_id=session_id)
            final_text = None
            async with asyncio.timeout(45):
                async for event in self._runner.run_async(
                    user_id=user_id, session_id=session_id,
                    new_message=types.Content(role="user", parts=[types.Part(text=trip.model_dump_json())]),
                    run_config=RunConfig(max_llm_calls=1),
                ):
                    if event.is_final_response() and event.content:
                        final_text = "".join(p.text or "" for p in event.content.parts or [] if not p.thought)
            choice = PlanChoice.model_validate_json(final_text or "")
            validate_choices(choice, trip)
            return choice, "Gemini through Google ADK"
        except asyncio.CancelledError:
            raise
        except Exception:
            # Do not return or log SDK errors: they may include prompts or secrets.
            raise PlanningUnavailable() from None
        finally:
            if self._sessions is not None:
                await self._sessions.delete_session(app_name="private_travel_planner",
                                                    user_id=user_id, session_id=session_id)
