# worlds.py

COUNTRY_RULES = {
    "United States": {
        "base_duty": 10,
        "risk": "low"
    },
    "India": {
        "base_duty": 18,
        "risk": "medium"
    },
    "UAE": {
        "base_duty": 5,
        "risk": "low"
    }
}


# -----------------------------
# Generate worlds
# -----------------------------
def generate_worlds(invoice, hs_data):
    worlds = []

    hs_codes = hs_data.get("all_hs_codes", [])[:3]

    for country, rules in COUNTRY_RULES.items():
        for code in hs_codes:

            duty = estimate_duty(code, rules["base_duty"])
            risk = assess_risk(code, rules["risk"])

            world = {
                "hs_code": code,
                "country": country,
                "estimated_duty": duty,
                "risk": risk
            }

            world["score"] = score_world(world)

            worlds.append(world)

    return worlds[:9]


# -----------------------------
# Duty logic
# -----------------------------
def estimate_duty(hs_code, base):
    if hs_code.startswith("62"):
        return base + 2
    elif hs_code.startswith("42"):
        return base + 8
    return base


# -----------------------------
# Risk logic
# -----------------------------
def assess_risk(hs_code, base_risk):
    if hs_code.startswith("42"):
        return "high"
    return base_risk


# -----------------------------
# Scoring
# -----------------------------
def score_world(world):
    score = 100

    score -= world["estimated_duty"]

    if world["risk"] == "high":
        score -= 20
    elif world["risk"] == "medium":
        score -= 10

    return score


# -----------------------------
# Select best
# -----------------------------
def select_best_world(worlds):
    if not worlds:
        return None

    return sorted(worlds, key=lambda x: x["score"], reverse=True)[0]