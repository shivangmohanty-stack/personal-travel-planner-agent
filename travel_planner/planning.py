"""Verified output boundary, local cost arithmetic, and a transparent demo planner."""

from .catalog import catalogue
from .guardrails import DayChoice, PlanChoice


def estimate_budget(trip):
    nights = trip.days - 1
    rooms = (trip.travelers + 1) // 2
    room_rate = 1200 if trip.stay == "economy" else 2200
    rows = [
        ("Accommodation", nights, rooms * room_rate, "night(s); rooms sharing two adults"),
        ("Food", trip.days * trip.travelers, 600, "person-day(s)"),
        ("Local transport", trip.days * trip.travelers, 500, "person-day(s)"),
        ("Entry allowance", trip.days * trip.travelers, 300, "person-day(s)"),
    ]
    items = [dict(category=name, quantity=qty, unit_cost=rate, amount=qty * rate, basis=basis)
             for name, qty, rate, basis in rows]
    subtotal = sum(item["amount"] for item in items)
    reserve = (subtotal + 9) // 10
    items.append(dict(category="Contingency (10%)", quantity=1, unit_cost=reserve,
                      amount=reserve, basis="rounded up to the next rupee"))
    total = subtotal + reserve
    return dict(items=items, total=total, remaining=trip.budget - total,
                feasible=total <= trip.budget, nights=nights, rooms=rooms,
                currency="INR")


def demo_choices(trip):
    """A catalog-only fallback for practice; never described as an AI response."""
    places = list(catalogue(trip.destination).values())[:-1]
    # Prioritize requested interests while grouping area labels where possible.
    places.sort(key=lambda item: (not (item[0] == "food" and "food" in trip.interests),
                                  item[2] not in trip.interests, item[3]))
    days = []
    for i in range(trip.days):
        # Reserve food for an evening slot, and keep the first two stops nearby.
        daytime = [p for p in places if p[0] != "food"]
        morning = daytime[0] if daytime else None
        if morning:
            places.remove(morning)
        nearby = [p for p in places if p[0] != "food" and morning and p[3] == morning[3]]
        other = [p for p in places if p[0] != "food"]
        afternoon = (nearby or other or [None])[0]
        if afternoon:
            places.remove(afternoon)
        evenings = [p for p in places if p[2] not in {"history", "culture"}]
        food = [p for p in evenings if p[0] == "food"]
        evening = (food or evenings or [None])[0]
        if evening:
            places.remove(evening)
        days.append(DayChoice(day=i + 1,
                              morning=morning[0] if morning else "rest",
                              afternoon=afternoon[0] if afternoon else "rest",
                              evening=evening[0] if evening else "rest"))
    return PlanChoice(days=days)


def validate_choices(choice, trip):
    if len(choice.days) != trip.days or [d.day for d in choice.days] != list(range(1, trip.days + 1)):
        raise ValueError("Day count or order is invalid.")
    allowed = catalogue(trip.destination)
    seen = set()
    for day in choice.days:
        if day.evening in allowed and allowed[day.evening][2] in {"history", "culture"}:
            raise ValueError("Ticketed historical visits belong in daytime slots.")
        for key in (day.morning, day.afternoon, day.evening):
            if key not in allowed or (key != "rest" and key in seen):
                raise ValueError("Unknown or repeated activity.")
            seen.add(key)
    if "food" in trip.interests and not any("food" in (d.morning, d.afternoon, d.evening) for d in choice.days):
        raise ValueError("The requested food interest is missing.")
    return choice


def render_plan(trip, choice, source):
    """All visible words come from code/catalog; Gemini cannot insert prose or HTML."""
    validate_choices(choice, trip)
    budget = estimate_budget(trip)
    places = catalogue(trip.destination)
    itinerary = []
    for day in choice.days:
        itinerary.append(dict(day=day.day, activities=[
            dict(time=slot.capitalize(), place=places[getattr(day, slot)][1],
                 area=places[getattr(day, slot)][3])
            for slot in ("morning", "afternoon", "evening")
        ]))
    return dict(
        trip=trip.model_dump(), itinerary=itinerary, budget=budget, source=source,
        assumptions=["Total group budget in INR; adults only.",
                     "Travel to/from the destination and shopping are excluded.",
                     "Hotel nights = days minus one; two adults share a room."],
        tips=["Costs are sample planning assumptions, not verified current prices.",
              "Confirm opening days, entry rules, prices, and routes before traveling.",
              "Free-time slots allow rest; this small catalog may not fill a long trip."],
    )
