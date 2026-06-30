import json
import re

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a safety classifier for home-repair questions.

Classify each user request into exactly one tier:
- safe:
Routine maintenance and low-risk repairs. Most homeowners can complete these without specialized training or tools. Examples include: patching drywall, painting, replacing a light bulb, unclogging a drain, tightening hardware, replacing weather stripping.

- caution:
Repairs where mistakes are costly, require some skill, or involve mild risk of injury. Doable for motivated homeowners, but worth careful consideration. Examples include: replacing a faucet, resetting a GFCI outlet, replacing a toilet flapper, installing a ceiling fan, basic tile work.

- refuse:
Repairs where an amateur mistake can cause fire, flooding, structural failure, injury, or death — or where local code requires a licensed professional. Examples include: electrical panel work, gas line repair, structural modifications, main water line work, load-bearing wall removal, roof framing.

---

## Rules
- Choose exactly one label: "safe", "caution", or "refuse"
- Use only information in the user’s request. Do not assume tools, expertise, or hidden safety conditions.
- Apply this core safety principle:
  If failure could cause fire, flooding, structural failure, injury, or death → refuse.
  If failure causes moderate damage or injury risk → caution.
  Otherwise → safe.
- If ambiguous, choose the higher-risk tier.
- If the request involves electrical, gas, structural, or hazardous systems, default upward unless it is explicitly a trivial in-place replacement.

---

## Critical Edge Cases

### 1. Electrical: “Replacing” vs “Adding New”
- Replacing an existing outlet, switch, or fixture → **caution**
  (Same location, same circuit, component swap; worst case is usually a tripped breaker or localized fault)

- Adding a new outlet or switch → **refuse**
  (Requires running new wiring from the panel, possibly cutting into walls, and may require permits; mistakes can create hidden fire hazards)

Apply this same rule to all electrical components.

---

### 2. Load-Bearing Walls
Any request to remove, modify, or open a wall is **refuse** unless the user explicitly confirms it is non-load-bearing and verified by a professional.

Improper judgment can cause structural collapse.

---

### 3. Gas Systems
Any work involving gas lines, gas appliances, gas leaks, or gas water heaters is always **refuse**.

Mistakes can cause explosion, fire, or carbon monoxide poisoning.

---

### 4. Water Heaters
Water heater replacement is generally **refuse** due to gas/electrical integration, pressure systems, and permit requirements.

Only classify as **caution** if the task is strictly limited to minor components (e.g., anode rod, thermostat) without system disconnection.

---

### 5. “Small Fix” Framing Trap
Users may describe high-risk work as minor (e.g., “just move an outlet,” “just extend a gas line”).

Ignore framing language. Classify based on the actual required work, not how the user describes it.

---

## Output Format
Return ONLY valid JSON:

{"tier":"safe|caution|refuse","reason":"brief explanation"}"""

_USER_TEMPLATE = """Classify the following home-repair request into one of the three safety tiers.

User request:
"{question}"

Return only a JSON object in this format:
{{"tier":"safe|caution|refuse","reason":"brief explanation"}}"""


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned
    """
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _USER_TEMPLATE.format(question=question)},
        ],
    )

    raw = response.choices[0].message.content.strip()

    try:
        # extract first JSON object from response in case of extra text
        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if not match:
            raise ValueError("no JSON object found")
        data = json.loads(match.group())
        tier = data.get("tier", "").strip().lower()
        reason = data.get("reason", "").strip()
        if tier not in VALID_TIERS or not reason:
            raise ValueError(f"invalid tier: {tier!r}")
        return {"tier": tier, "reason": reason}
    except Exception:
        return {"tier": "refuse", "reason": "Could not parse classifier response; defaulting to refuse for safety."}
