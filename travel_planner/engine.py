"""Run the live ADK agent with an isolated temporary session per request."""
import asyncio
import os
import re
import uuid
from decimal import Decimal
from travel_planner.guardrails import TravelAnswer

class PlanningUnavailable(Exception):
    """Generic error: never expose SDK payloads or private settings."""

def format_reply(reply):
    """Sum Gemini's variable estimates in Python; there are no preset rates."""
    text = re.sub(
        r"(?ims)^#{1,6}\s+(?:estimated budget|budget breakdown|budget|cost estimate)\s*:?\s*\n.*?(?=^#{1,6}\s|\Z)",
        "", reply.answer,
    ).split("\nEstimated budget (", 1)[0].rstrip()
    if reply.status != "answer" or reply.budget is None:
        return text
    budget = reply.budget
    total = sum((Decimal(str(item.amount)).quantize(Decimal("0.01")) for item in budget.items), Decimal(0))
    rows = [f"\n\nEstimated budget ({budget.currency}) — estimates, not live quotes"]
    for item in budget.items:
        amount = Decimal(str(item.amount)).quantize(Decimal("0.01"))
        rows.append(f"• {item.category}: {amount:,.2f} — {item.assumption}")
    rows.append(f"Estimated total: {budget.currency} {total:,.2f}")
    if budget.limit is not None:
        remaining = Decimal(str(budget.limit)).quantize(Decimal("0.01")) - total
        label = "Remaining budget" if remaining >= 0 else "Over budget"
        rows.append(f"{label}: {budget.currency} {abs(remaining):,.2f}")
    return text + "\n".join(rows)

class Planner:
    def __init__(self):
        self._runner = None
        self._sessions = None

    @property
    def model(self):
        return os.getenv("TRAVEL_MODEL", "gemini-3.5-flash-lite")

    def _initialize(self):
        if self._runner is not None:
            return
        if not os.getenv("GOOGLE_API_KEY"):
            raise PlanningUnavailable()
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from .agent import root_agent
        self._sessions = InMemorySessionService()
        self._runner = Runner(agent=root_agent, app_name="private_travel_planner", session_service=self._sessions)

    async def reply(self, message, history, user_id):
        session_id = uuid.uuid4().hex
        try:
            self._initialize()
            from google.genai import types
            from google.adk.agents.run_config import RunConfig
            await self._sessions.create_session(app_name="private_travel_planner", user_id=user_id,
                session_id=session_id, state={"travel_context": history[-12:]})
            final_text = None
            async with asyncio.timeout(100):
                async for event in self._runner.run_async(user_id=user_id, session_id=session_id,
                    new_message=types.Content(role="user", parts=[types.Part(text=message)]),
                    run_config=RunConfig(max_llm_calls=1)):
                    if event.is_final_response() and event.content:
                        final_text = "".join(p.text or "" for p in event.content.parts or [] if not p.thought)
            return TravelAnswer.model_validate_json(final_text or "")
        except asyncio.CancelledError:
            raise
        except Exception:
            raise PlanningUnavailable() from None
        finally:
            if self._sessions is not None:
                await self._sessions.delete_session(app_name="private_travel_planner", user_id=user_id, session_id=session_id)
