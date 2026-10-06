"""Privacy checks and response schemas; no city or price catalogs."""
import re
import unicodedata
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

REFUSAL = (
    "I can help create and improve travel itineraries, including places to visit, "
    "accommodation, food, transport, and estimated budgets. "
    "Please keep your request related to planning a trip."
)
PRIVATE = "Please remove passwords, API keys, contact details, or identity numbers before sending your travel request."
HELP = "Tell me where you want to go, for how long, your budget, and what you enjoy. You can also ask me to change an existing itinerary."
# Catch recognizable secrets, not ordinary travel vocabulary.
SECRET = re.compile(
    r"AIza[\w-]{20,}|AQ\.[\w-]{20,}|sk-[\w-]{16,}|"
    r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|"
    r"\b(?:password|api[ _-]?key|access token|private key|"
    r"passport number|aadhaar|aadhar|credit card|bank account)\s*[:=]\s*\S+|"
    r"(?<![\w.])(?:\+?\d[ -]?){10,16}(?![\w.])", re.I,
)
INJECTION = re.compile(
    r"\b(?:ignore|override|bypass)\s+(?:(?:all|the|your|previous|above|system|developer)\s+)*"
    r"(?:instructions|rules|guardrails|safety)\b|"
    r"\b(?:reveal|show|print|dump|expose)\s+(?:(?:me|the|your|all|hidden|private)\s+)*"
    r"(?:system prompt|developer message|credentials|api keys?|passwords?)\b|"
    r"\b(?:another|other|someone else's)\s+users?'?s?\s+(?:chats?|history|data)\b", re.I,
)

def inspect_message(raw):
    """Block recognizable secrets/attacks locally; Gemini judges travel intent."""
    if not isinstance(raw, str) or not raw.strip():
        return HELP
    if len(raw) > 4000:
        return "Please shorten the message to 4000 characters."
    text = unicodedata.normalize("NFKC", raw)
    if any(unicodedata.category(c) in {"Cc", "Cf"} and c not in "\n\t" for c in text):
        return REFUSAL
    if SECRET.search(text):
        return PRIVATE
    if INJECTION.search(text):
        return REFUSAL
    return None

class ScopeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed: StrictBool

class CostItem(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    category: str = Field(min_length=1, max_length=120)
    amount: float = Field(ge=0)
    assumption: str = Field(min_length=1, max_length=400)

class Budget(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    limit: float | None = Field(default=None, gt=0)
    items: list[CostItem] = Field(min_length=1, max_length=20)

class TravelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["answer", "clarification", "refusal"]
    answer: str = Field(min_length=1, max_length=24000)
    budget: Budget | None = None

class TripForm(BaseModel):
    """Optional form; chat can also describe the entire trip naturally."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)
    destination: str = Field(min_length=1, max_length=120)
    days: StrictInt = Field(ge=1)
    travelers: StrictInt = Field(default=1, ge=1)
    budget: float | None = Field(default=None, gt=0)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    interests: str = Field(default="", max_length=500)
    accommodation: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=1000)

    def message(self):
        price = f"{self.currency} {self.budget:g}" if self.budget else "not decided; suggest an estimate"
        return (
            f"Plan a {self.days}-day trip to {self.destination} for {self.travelers} traveler(s). "
            f"Total trip budget: {price}. Interests: {self.interests or 'suggest a balanced itinerary'}. "
            f"Accommodation preference: {self.accommodation or 'suggest suitable options'}. "
            f"Additional trip preferences: {self.notes or 'none'}. "
            "Give a day-wise itinerary, explain your recommendations, and estimate the budget."
        )
