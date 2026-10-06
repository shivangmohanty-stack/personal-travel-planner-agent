"""Input allowlists and schemas. Only TripSpec values may reach Gemini."""

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from .catalog import INTERESTS, PLACES

REFUSAL = (
    "I only create and revise travel itineraries and estimated budgets. "
    "I can't answer weather, office-distance, general questions, or requests "
    "for private data. Use the trip form or the example travel request."
)
PRIVATE = (
    "Please remove personal or secret details. I only need a destination, "
    "days, total budget, traveler count, interests, and stay preference."
)
HELP = (
    "Use the trip form, or try: Plan a 3-day trip to Jaipur with a budget of "
    "₹15000. I like history and local food. For revisions: make it 2 days; "
    "set budget to 10000; interests: history and food; or destination: Udaipur."
)


class TripSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    destination: Literal["Jaipur", "Udaipur", "Mysuru", "Goa", "Delhi", "Agra"]
    days: StrictInt = Field(ge=1, le=7)
    budget: StrictInt = Field(ge=100, le=1_000_000)
    travelers: StrictInt = Field(default=1, ge=1, le=6)
    interests: list[Literal["history", "food", "culture", "nature", "photography", "shopping"]] = Field(min_length=1, max_length=6)
    stay: Literal["economy", "standard"] = "economy"


class DayChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day: StrictInt = Field(ge=1, le=7)
    morning: str = Field(pattern=r"^[a-z]{2,20}$")
    afternoon: str = Field(pattern=r"^[a-z]{2,20}$")
    evening: str = Field(pattern=r"^[a-z]{2,20}$")


class PlanChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: list[DayChoice] = Field(min_length=1, max_length=7)


# Reject rather than transmit sensitive messages. This is a heuristic, not DLP.
SECRET = re.compile(
    r"AIza[\w-]{20,}|AQ\.[\w-]{20,}|sk-[\w-]{16,}|"
    r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|https?://|www\.|"
    r"\b(?:password|api[ _-]?key|passport|aadhaar|aadhar|credit card|"
    r"bank account|phone number|mobile number|my address|home address|"
    r"access token|private key|secret key)\b|"
    r"(?<!\d)(?:\+?\d[ -]?){10,16}(?!\d)", re.I,
)
OUTSIDE = re.compile(
    r"\b(?:weather|temperature|forecast|rain|rainfall|office|commute|"
    r"how far|distance|code|coding|python|politics|election|stock|"
    r"ignore|override|jailbreak|system prompt|developer message|"
    r"instructions|reveal|dump|other users?|someone else|another user|"
    r"all chats|chat history|sessions?|credentials|base64|execute|"
    r"eval|shell|curl|sql|hack|steal|weapon|illegal|bypass)\b", re.I,
)


def inspect_message(raw):
    """Return a safe local reply if the message must not be processed."""
    if not isinstance(raw, str) or not raw.strip():
        return HELP
    if len(raw) > 1000:
        return "Please shorten the request to 1000 characters or use the trip form."
    text = unicodedata.normalize("NFKC", raw)
    if any(unicodedata.category(c) in {"Cc", "Cf"} and c not in "\n\t" for c in text):
        return REFUSAL
    if SECRET.search(text):
        return PRIVATE
    if OUTSIDE.search(text):
        return REFUSAL
    return None


def _interests(text):
    text = text.strip(" .!").lower()
    text = re.sub(r"\b(?:i|am|like|enjoy|interested|in|and|local|vegetarian|my|interests|are)\b", " ", text)
    text = text.replace("&", " ").replace(",", " ").replace(":", " ")
    values = text.split()
    if not values or any(value not in INTERESTS for value in values):
        raise ValueError("Choose the interests offered in the trip form.")
    return list(dict.fromkeys(values))


def parse_message(raw, previous=None):
    """Accept a small documented grammar. Unknown text fails closed."""
    blocked = inspect_message(raw)
    if blocked:
        return None, blocked
    text = unicodedata.normalize("NFKC", raw).strip().lower()
    if text in {"help", "hi", "hello", "what can you do", "what can you do?"}:
        return None, HELP
    cities = "|".join(city.lower() for city in PLACES)
    # Two intentionally bounded templates, not a general-purpose classifier.
    pattern = (
        rf"(?:i want to visit|visit|travel to) (?P<city>{cities}) for (?P<days>\d+) days? "
        rf"with (?:a |an )?(?:total )?budget of (?:₹|rs\.?\s*|inr\s*)?(?P<budget>[\d,]+)[.!]?\s+"
        rf"(?P<interests>(?:i like|i enjoy|i am interested in|interests:) .+)"
    )
    alternate = (
        rf"plan (?:a |an )?(?P<days>\d+)[ -]day trip to (?P<city>{cities}) "
        rf"with (?:a |an )?(?:total )?budget of (?:₹|rs\.?\s*|inr\s*)?(?P<budget>[\d,]+)[.!]?\s+"
        rf"(?P<interests>(?:i like|i enjoy|i am interested in|interests:) .+)"
    )
    match = re.fullmatch(pattern, text) or re.fullmatch(alternate, text)
    try:
        if match:
            data = match.groupdict()
            return TripSpec(
                destination=next(c for c in PLACES if c.lower() == data["city"]),
                days=int(data["days"]), budget=int(data["budget"].replace(",", "")),
                interests=_interests(data["interests"]),
            ), None
        if previous:
            data = previous.model_dump()
            if match := re.fullmatch(r"(?:make it|change to) (\d+) days?[.!]?", text):
                data["days"] = int(match[1])
            elif match := re.fullmatch(r"set budget to (?:₹|rs\.?\s*|inr\s*)?([\d,]+)[.!]?", text):
                data["budget"] = int(match[1].replace(",", ""))
            elif match := re.fullmatch(r"travelers: (\d+)[.!]?", text):
                data["travelers"] = int(match[1])
            elif match := re.fullmatch(rf"destination: ({cities})[.!]?", text):
                data["destination"] = next(c for c in PLACES if c.lower() == match[1])
            elif text.startswith("interests: "):
                data["interests"] = _interests(text)
            elif match := re.fullmatch(r"stay: (economy|standard)[.!]?", text):
                data["stay"] = match[1]
            else:
                return None, REFUSAL + " " + HELP
            return TripSpec.model_validate(data), None
    except (ValueError, OverflowError):
        return None, "Choose a supported city, 1–7 days, ₹100–₹1000000, 1–6 travelers, and listed interests."
    return None, REFUSAL + " " + HELP
