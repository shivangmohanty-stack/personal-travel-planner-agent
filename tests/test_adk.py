"""Real ADK callbacks with model doubles; these are NOT offline app responses."""
import asyncio
from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import PrivateAttr
import pytest
import agent as implementation
from travel_planner.guardrails import REFUSAL, TravelAnswer

class LocalModel(BaseLlm):
    _requests: list = PrivateAttr(default_factory=list)
    _answer: str = PrivateAttr(default="")
    async def generate_content_async(self, llm_request, stream=False):
        self._requests.append(llm_request)
        yield LlmResponse(content=types.Content(role="model", parts=[
            types.Part(text="private-thought", thought=True), types.Part(text=self._answer)
        ]), partial=False)

def run_adk(raw, answer, monkeypatch, allow_input=True, allow_output=True, history=None):
    checks = []
    async def checker(payload):
        checks.append(payload)
        return allow_output if payload["review"] else allow_input
    monkeypatch.setattr(implementation, "check_scope", checker)
    async def run():
        model = LocalModel(model="local-test-model"); model._answer = answer
        agent = Agent(name="personal_travel_planner", model=model, instruction=implementation.root_agent.instruction,
            output_schema=TravelAnswer, before_model_callback=implementation.before_model, after_model_callback=implementation.after_model)
        service = InMemorySessionService()
        await service.create_session(app_name="test_private_planner", user_id="opaque-user", session_id="isolated",
                                     state={"travel_context":history or []})
        runner = Runner(agent=agent, app_name="test_private_planner", session_service=service)
        parts = []
        async for event in runner.run_async(user_id="opaque-user", session_id="isolated",
            new_message=types.Content(role="user", parts=[types.Part(text=raw)])):
            if event.is_final_response() and event.content:
                parts.extend(event.content.parts)
        await service.delete_session(app_name="test_private_planner", user_id="opaque-user", session_id="isolated")
        assert await service.get_session(app_name="test_private_planner", user_id="opaque-user", session_id="isolated") is None
        return model._requests, parts, checks
    return asyncio.run(run())

def test_natural_hotel_followup_reaches_adk_with_only_own_history(monkeypatch):
    history=[{"role":"user","text":"Plan 12 days in Kyoto"}, {"role":"assistant","text":"Your Kyoto itinerary"}]
    answer=TravelAnswer(status="answer",answer="Here are 4-star accommodation options for your Kyoto trip.")
    requests, parts, checks=run_adk("Add a 4-star hotel",answer.model_dump_json(),monkeypatch,history=history)
    assert len(requests)==1 and len(checks)==2
    assert [c.parts[0].text for c in requests[0].contents] == [h["text"] for h in history]+["Add a 4-star hotel"]
    assert not any(p.thought for p in parts)
    assert "4-star" in "".join(p.text for p in parts)

@pytest.mark.parametrize("message", ["Write a Python script", "How far is my office?", "What is today's weather?"])
def test_intent_checker_can_stop_outside_requests_before_planner(monkeypatch,message):
    requests,parts,checks=run_adk(message,"unsafe",monkeypatch,allow_input=False)
    assert requests==[] and len(checks)==1
    assert TravelAnswer.model_validate_json(parts[0].text).answer==REFUSAL

def test_local_privacy_check_makes_no_model_calls(monkeypatch):
    requests,parts,checks=run_adk("My email is private@example.com","unsafe",monkeypatch)
    assert requests==[] and checks==[] and "private@example.com" not in parts[0].text

def test_output_review_blocks_off_topic_answer(monkeypatch):
    value=TravelAnswer(status="answer",answer="Off-topic content")
    _,parts,checks=run_adk("Plan Jaipur",value.model_dump_json(),monkeypatch,allow_output=False)
    assert len(checks)==2 and "Off-topic content" not in parts[0].text

@pytest.mark.parametrize("answer", ['{"answer":"invalid"}', TravelAnswer(status="answer",answer="api key: PRIVATESECRET").model_dump_json()])
def test_malformed_or_secret_output_is_not_returned(monkeypatch,answer):
    with pytest.raises(ValueError):
        run_adk("Plan Jaipur",answer,monkeypatch)

def test_scope_failure_stops_planner_and_never_disables_the_guardrail(monkeypatch):
    async def broken(payload):
        raise RuntimeError("private-sdk-error")
    async def run():
        model=LocalModel(model="local-test-model")
        service=InMemorySessionService()
        await service.create_session(app_name="failure_test",user_id="user",session_id="failure")
        test_agent=Agent(name="travel_test",model=model,before_model_callback=implementation.before_model)
        runner=Runner(agent=test_agent,app_name="failure_test",session_service=service)
        with pytest.raises(RuntimeError):
            async for _ in runner.run_async(user_id="user",session_id="failure",
                new_message=types.Content(role="user",parts=[types.Part(text="Plan a trip")])):
                pass
        assert model._requests==[]
    monkeypatch.setattr(implementation,"check_scope",broken)
    asyncio.run(run())

def test_transport_schema_is_compatible_and_local_validation_stays_strict():
    from google.genai import _transformers
    schema=implementation.transport_schema(TravelAnswer)
    wire=_transformers.t_schema(None,schema)
    assert wire.properties["budget"].properties["currency"].type.value=="STRING"
