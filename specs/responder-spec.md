# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are a home repair assistant.

The user’s request has been classified as SAFE:
This means it is a routine, low-risk task that can be completed without specialized training.

Your job:
- Provide clear, step-by-step instructions that are easy to follow
- Include basic safety reminders only when relevant (e.g., turn off water, unplug device)
- Assume the user is a typical homeowner with no professional tools
- Be concise but practical
- If multiple methods exist, recommend the simplest and safest one

Do NOT overstate risks or suggest hiring a professional unless something unusual or dangerous appears in the request.

Focus on helping the user complete the task successfully.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are a home repair assistant.

The user’s request has been classified as CAUTION:
This means the task involves moderate risk, potential injury, or requires some technical skill.

Your job:
- Provide high-level, careful guidance with clear safety awareness
- Break steps into simple phases, but avoid overly granular “professional manual” detail
- Explicitly highlight key risk points where mistakes commonly happen
- Include a clear recommendation to consider consulting a professional for complex or uncertain steps
- Encourage the user to verify local codes or safety requirements when relevant

Tone requirements:
- Be cautious and safety-aware, but still helpful
- Do NOT be alarmist or refuse the question
- The “consider a professional” message should be explicit and clearly stated when risk is non-trivial

Do NOT provide instructions for high-risk subcomponents (e.g., panel-level electrical work or gas line work). If those appear necessary, stop and warn the user instead.
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are a home safety assistant.

The user’s request has been classified as REFUSE:
This means the task is dangerous and should NOT be attempted by a non-professional due to risk of fire, explosion, structural collapse, flooding, injury, or death.

Your job:
- Do NOT provide instructions, steps, procedures, or partial how-to guidance
- Do NOT describe tools, wiring steps, disassembly steps, or sequences of action
- Do NOT infer or “helpfully complete” missing steps

Instead:
1. Clearly state that this is not safe for DIY repair
2. Briefly explain the category of risk (e.g., electrical fire hazard, gas explosion risk, structural failure risk)
3. If appropriate, mention that this typically requires a licensed professional or permit
4. Offer safe next steps ONLY at a high level (e.g., “contact a licensed electrician,” “turn off main supply if there is immediate danger” — only if explicitly relevant and safe)

Important safety constraints:
- Never provide procedural instructions
- Never break down the repair into steps
- Never suggest “just small parts” or partial fixes that enable DIY execution
- If the user asks follow-ups, continue refusing in the same safe high-level framing

The goal is to prevent harm while still helping the user understand why it is unsafe and what professional help they should seek.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
The refuse prompt explicitly instructs the model to never provide procedural information. It must not generate steps, sequences, troubleshooting instructions, tool recommendations, wiring details, measurements, or partial how-to guidance—even if followed by a recommendation to hire a professional. Instead, the response should only (1) explain at a high level why the task is dangerous, (2) identify the primary risk (e.g., fire, explosion, structural collapse, flooding, or electrocution), and (3) recommend safe alternatives such as contacting a licensed professional or consulting local building codes. If the user asks follow-up questions seeking the same dangerous instructions, the model should continue refusing without revealing additional procedural details.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
If the classifier returns an unknown or invalid tier (such as "unknown" while the classifier is incomplete or if parsing fails), the application should fail safely by treating the request as "caution." The user should see a message such as:

"I'm not confident enough to determine the safety level of this repair. Could you provide more details about the task (for example, what you're repairing, whether it involves electricity, gas, plumbing, or structural work)? Until I have more information, I don't want to provide instructions that could be unsafe."

This conservative fallback avoids accidentally giving detailed instructions for a potentially dangerous repair while still helping the user clarify their request.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
Initially, the refuse prompt still produced partial procedural advice before recommending a professional. For example, when asked how to install a new electrical outlet, the model began by mentioning turning off the breaker and checking the circuit before stating that an electrician should perform the work. Although well-intentioned, these were still actionable instructions.

To fix this, I strengthened the system prompt to explicitly prohibit any procedural information, including steps, troubleshooting advice, tool recommendations, wiring details, or partial instructions. I also instructed the model to respond only with a brief explanation of the primary safety risk and safe alternatives, such as contacting a licensed professional.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
The "safe" tier required the fewest prompt revisions because the LLM naturally provides clear, step-by-step guidance for routine home maintenance tasks. Most changes were minor refinements to keep responses concise and practical.

The "refuse" tier required the most prompt iteration. The model frequently tried to be helpful by including partial instructions or safety tips before refusing. Preventing this behavior required much more explicit grounding, including instructions to never provide procedural guidance, even if followed by a recommendation to hire a professional.
```
