import json
from typing import Dict, Any

from app.models.db import SessionLocal, Conversation


def get_state(session_id: str) -> Dict[str, Any]:
    """Get saved environmental information for a chat session."""

    db = SessionLocal()

    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .first()
        )

        if not conversation:
            return {}

        try:
            return json.loads(conversation.state_json)
        except json.JSONDecodeError:
            return {}

    finally:
        db.close()


def save_state(session_id: str, state: Dict[str, Any]) -> None:
    """Save environmental information for a chat session."""

    db = SessionLocal()

    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .first()
        )

        state_json = json.dumps(state)

        if conversation:
            conversation.state_json = state_json
        else:
            conversation = Conversation(
                session_id=session_id,
                state_json=state_json
            )
            db.add(conversation)

        db.commit()

    finally:
        db.close()


def merge_state(
    old_state: Dict[str, Any],
    new_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge new environmental information into existing session memory.

    None values do not overwrite information already remembered.
    """

    merged = dict(old_state)

    for key, value in new_state.items():

        if value is not None and value != "":
            merged[key] = value

    return merged