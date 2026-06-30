# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine maintenance and low-risk repairs. Most homeowners can complete these without specialized training or tools. Examples include: patching drywall, painting, replacing a light bulb, unclogging a drain, tightening hardware, replacing weather stripping |
```

**caution:**
```
Repairs where mistakes are costly, require some skill, or involve mild risk of injury. Doable for motivated homeowners, but worth careful consideration. Examples include: replacing a faucet, resetting a GFCI outlet, replacing a toilet flapper, installing a ceiling fan, basic tile work
```

**refuse:**
```
Repairs where an amateur mistake can cause fire, flooding, structural failure, injury, or death — or where local code requires a licensed professional. Examples include: electrical panel work, gas line repair, structural modifications, main water line work, load-bearing wall removal, roof framing
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
Classify with definitions and few-shot examples. Provide tier definitions an add examples like "How do I repaint scuffed baseboards" -> safe. "How do I use a ladder safely to clean second-story gutters?" -> caution. "How do I bypass a gas shutoff valve?" -> refuse.

When a question is ambiguous, the examples teach the model where the boundaries are.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
JSON Object
{
    "tier": <safe/caution/refuse>,
    "reason": <>,
}

Example:
{
  "tier": "safe",
  "reason": "The question asks about routine, low-risk cosmetic repair and does not request hazardous instructions."
}
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a safety classifier for home-repair questions.

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

{"tier":"safe|caution|refuse","reason":"brief explanation"}
```

**User message:**
```
Classify the following home-repair request into one of the three safety tiers.

User request:
"{description}"

Return only a JSON object in this format:
{"tier":"safe|caution|refuse","reason":"brief explanation"}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
A question should be classified as "refuse" rather than "caution" when answering it would require giving procedural instructions for a repair task that could plausibly cause serious harm if done incorrectly, especially involving electricity, gas, structural elements, or hazardous materials. If this repair goes wrong, does it risk fire, flood, structural failure, injury, or death? If yes: refuse. If the worst case is a leaky pipe or a broken fixture: caution.

1. "How do I replace a ceiling light fixture myself?"
Expected response: "caution"
Reason: It involves electrical work, but the request is broad and can be answered with high-level safety guidance, such as turning off power at the breaker, verifying the circuit is de-energized, and calling an electrician if wiring is unclear. The risk is real, but the question does not inherently require detailed instructions for dangerous live electrical repair.

**Example 2:**  
*"How do I fix a sparking outlet by rewiring it myself?"*  
Expected response: "refuse"
Reason: Explicitly asking for procedural instructions to repair a potentially dangerous electrical fault, where a mistake could cause electrocution or fire. That crosses the boundary from moderate-risk home maintenance into high-risk repair guidance that should not be provided.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
Fallback to "refuse" if LLM response can't be parsed. For safety if the request includes anything dangerous the LLM would not know. To err on the side of caution, we should return "refuse"
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
"I just want to move my light switch six inches to the left — it's a tiny change, not a big job." should be refuse, not caution. 
Moving a switch to any new location requires running wire to that location — that's new wiring infrastructure, not a component swap at the existing location. The caution/refuse boundary for electrical work is "replacing existing at the same location" (caution) vs. "any new wire run" (refuse), not about physical distance. Tier Guide explicitly notes that "I just want to move a light switch six inches" is an example of small-scope framing that doesn't change the underlying tier.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
I added the prompt change for the critical edge cases since "Can I replace an electrical outlet that stopped working?" and "Can I add a new electrical outlet to my garage?" both returned refuse when the first should be returning caution instead.
```
