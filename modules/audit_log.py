import pandas as pd
from datetime import datetime

REQUIRED_COLUMNS = [
    "timestamp", "user_id", "user_role", "action", "target_tab", 
    "target_key", "field", "old_value", "new_value", "status", 
    "source", "notes"
]

def build_audit_event(user_id, user_role, action, target_tab="", target_key="", field="", 
                      old_value="", new_value="", status="success", source="streamlit", notes=""):
    """
    Builds a dictionary representing an audit log event with standardized keys.
    """
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": str(user_id),
        "user_role": str(user_role),
        "action": str(action),
        "target_tab": str(target_tab),
        "target_key": str(target_key),
        "field": str(field),
        "old_value": str(old_value),
        "new_value": str(new_value),
        "status": str(status),
        "source": str(source),
        "notes": str(notes)
    }
    return event

def format_audit_event_text(event):
    """
    Formats an audit event dictionary into a clean, human-readable string.
    """
    parts = [
        f"[{event['timestamp']}] {event['user_role'].upper()} ({event['user_id']}) performed {event['action']}",
        f"Source: {event['source']}"
    ]
    if event['target_tab']:
        parts.append(f"Target Tab: {event['target_tab']}")
    if event['target_key']:
        parts.append(f"Target Key: {event['target_key']}")
    if event['field']:
        parts.append(f"Field: {event['field']} ({event['old_value']} -> {event['new_value']})")
    parts.append(f"Status: {event['status'].upper()}")
    if event['notes']:
        parts.append(f"Notes: {event['notes']}")
        
    return " | ".join(parts)

def validate_audit_log_schema(df):
    """
    Validates that a pandas DataFrame contains all required audit log columns.
    Returns (is_valid, missing_columns_list).
    """
    if not isinstance(df, pd.DataFrame):
        return False, ["Not a pandas DataFrame"]
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return len(missing) == 0, missing
