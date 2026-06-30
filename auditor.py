import json
import os
from datetime import datetime, timezone
from config import LOG_FILE


def log_interaction(question: str, tier: str, response: str) -> None:
    """
    Append a structured record of this interaction to the audit log (LOG_FILE).
    Creates the logs/ directory if it doesn't exist.
    Prints a one-line summary to the terminal.
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    record = {
        "timestamp": timestamp,
        "tier": tier,
        "question": question[:300],
        "response_preview": response[:200],
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    ts_short = timestamp[:19].replace("T", " ")
    print(f"[{ts_short}] tier={tier} | ({len(question)} chars) → {len(response)} chars response")
