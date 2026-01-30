import json
import os
import uuid
from datetime import datetime
from typing import Dict, List

LOG_FILE = os.path.join("logs", "experiment_data.json")

# ---- Mirrors logger.py ----
VALID_ACTIONS = {
    "CODE_ANALYSIS",
    "CODE_GEN",
    "DEBUG",
    "FIX"
}

VALID_STATUS = {"SUCCESS", "FAILURE"}

AGENT_ACTION_CONTRACT = {
    "Auditor": {"CODE_ANALYSIS"},
    "Fixer": {"FIX", "CODE_GEN"},
    "Judge": {"DEBUG"}
}

REQUIRED_DETAILS_FIELDS = {"input_prompt", "output_response"}


# ---------------- BASIC CHECKS ---------------- #

def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def is_valid_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def non_empty_string(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


# ---------------- PER-ACTION VALIDATION ---------------- #

def validate_action(entry: Dict, index: int):
    required_fields = {
        "id": str,
        "timestamp": str,
        "agent": str,
        "model": str,
        "action": str,
        "details": dict,
        "status": str
    }

    # 1️⃣ Required fields & types
    for field, ftype in required_fields.items():
        if field not in entry:
            raise ValueError(f"❌ Entry {index}: Missing field '{field}'")
        if not isinstance(entry[field], ftype):
            raise TypeError(
                f"❌ Entry {index}: Field '{field}' must be {ftype.__name__}"
            )

    # 2️⃣ UUID
    if not is_valid_uuid(entry["id"]):
        raise ValueError(f"❌ Entry {index}: Invalid UUID")

    # 3️⃣ Timestamp
    if not is_valid_iso_timestamp(entry["timestamp"]):
        raise ValueError(f"❌ Entry {index}: Invalid timestamp")

    # 4️⃣ Action & status
    if entry["action"] not in VALID_ACTIONS:
        raise ValueError(f"❌ Entry {index}: Invalid action '{entry['action']}'")

    if entry["status"] not in VALID_STATUS:
        raise ValueError(f"❌ Entry {index}: Invalid status '{entry['status']}'")

    # 5️⃣ Mandatory non-empty details
    for key in REQUIRED_DETAILS_FIELDS:
        if key not in entry["details"]:
            raise ValueError(f"❌ Entry {index}: Missing details.{key}")
        if not non_empty_string(entry["details"][key]):
            raise ValueError(f"❌ Entry {index}: details.{key} is empty")

    # 6️⃣ Agent ↔ Action contract
    agent = entry["agent"]
    if agent in AGENT_ACTION_CONTRACT:
        if entry["action"] not in AGENT_ACTION_CONTRACT[agent]:
            raise ValueError(
                f"❌ Entry {index}: Agent '{agent}' cannot perform '{entry['action']}'"
            )


# ---------------- FINAL (GLOBAL) VALIDATION ---------------- #

def validate_global_consistency(entries: List[Dict]):
    actions = [e["action"] for e in entries]
    agents = [e["agent"] for e in entries]
    statuses = [e["status"] for e in entries]
    models = {e["model"] for e in entries}

    # Mandatory actions
    if "CODE_ANALYSIS" not in actions:
        raise ValueError("❌ No CODE_ANALYSIS action found (Auditor never worked)")

    # Mandatory agents
    if "Auditor" not in agents:
        raise ValueError("❌ Auditor never logged an action")

    if "Fixer" not in agents:
        raise ValueError("❌ Fixer never logged an action")

    # Swarm outcome sanity
    if "SUCCESS" not in statuses:
        raise ValueError("❌ Swarm ended without any SUCCESS status")

    # Scientific traceability
    if not models:
        raise ValueError("❌ No model usage recorded")

    print(f"ℹ️ Models used during experiment: {models}")


# ---------------- MAIN ENTRY POINT ---------------- #

def validate_experiment_data():
    if not os.path.exists(LOG_FILE):
        raise FileNotFoundError("❌ experiment_data.json not found")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Invalid JSON format: {e}")

    if not isinstance(data, list) or not data:
        raise ValueError("❌ experiment_data.json must be a non-empty list")

    seen_ids = set()

    for index, entry in enumerate(data):
        validate_action(entry, index)

        # Duplicate ID detection
        if entry["id"] in seen_ids:
            raise ValueError(f"❌ Duplicate ID detected: {entry['id']}")
        seen_ids.add(entry["id"])

    validate_global_consistency(data)

    print("✅ experiment_data.json is FULLY VALIDATED (per-action + global)")


if __name__ == "__main__":
   validate_experiment_data()
