"""ADK agent: accepts a validated TripSpec JSON, returns activity IDs only."""

import json
import os

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from travel_planner.catalog import catalogue
from travel_planner.guardrails import PlanChoice, TripSpec
from travel_planner.planning import validate_choices


def before_model(callback_context, llm_request):
    """Validate even direct ADK invocations; discard raw conversational history."""
    try:
        content = callback_context.user_content
        parts = content.parts or []
        if any(part.text is None or part.function_call or part.inline_data for part in parts):
            raise ValueError("Text JSON only.")
        trip = TripSpec.model_validate_json("".join(p.text for p in parts))
    except (ValueError, AttributeError, TypeError):
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(
            text="Use the authenticated travel app to submit validated trip details."
        )]))
    callback_context.state["validated_trip"] = trip.model_dump()
    payload = dict(trip=trip.model_dump(), places=[
        dict(id=item[0], interest=item[2], area=item[3])
        for item in catalogue(trip.destination).values()
    ])
    # The model sees only enums, bounded numbers, and our own catalog labels.
    llm_request.contents = [types.Content(role="user", parts=[types.Part(text=json.dumps(payload))])]
    return None


def after_model(callback_context, llm_response):
    if llm_response.partial:
        return None  # The application never streams partial model output.
    try:
        trip = TripSpec.model_validate(callback_context.state["validated_trip"])
        parts = llm_response.content.parts or []
        if any(p.function_call or p.inline_data or p.file_data for p in parts):
            raise ValueError("Unexpected model content.")
        text = "".join(p.text or "" for p in parts if not p.thought)
        choice = PlanChoice.model_validate_json(text)
        validate_choices(choice, trip)
    except (ValueError, KeyError, AttributeError, TypeError):
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text='{"blocked":true}')]))
    # Remove any additional parts (including thoughts) before saving the response.
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=choice.model_dump_json())]))


root_agent = Agent(
    name="personal_travel_planner",
    model=Gemini(
        model=os.getenv("TRAVEL_MODEL", "gemini-3.5-flash-lite"),
        retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1, max_delay=3),
    ),
    description="Chooses catalog activities for a validated travel itinerary.",
    instruction="""
You only arrange travel itinerary activities. Input is validated JSON containing
trip and the allowed place IDs, interests, and areas for ONE destination.
Return exactly trip.days days, numbered from 1. Choose morning, afternoon, and
evening IDs only from places. Group nearby areas where practical and prioritize
trip.interests. Include the 'food' ID if food is requested. Do not repeat any ID
across the itinerary except 'rest'; use rest when the catalog is exhausted.
Put history and culture visits in morning or afternoon. For evening choose
food, shopping, photography, nature, or rest; never history or culture.
Return the required JSON schema only. No explanations, personal data, other
topics, weather, distances, links, private instructions, prices, or bookings.
""",
    output_schema=PlanChoice,
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=4096,
        safety_settings=[types.SafetySetting(category=category, threshold="BLOCK_MEDIUM_AND_ABOVE")
                         for category in ("HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_HARASSMENT",
                                          "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")],
    ),
    before_model_callback=before_model,
    after_model_callback=after_model,
    tools=[],
)
