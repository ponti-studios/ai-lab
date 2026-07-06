import uuid
from typing import List

from sqlalchemy.orm import Session

from src.data.models import Note
from src.utils.logger import logger


def create_note(session: Session, content: str, profile_id: uuid.UUID) -> Note | None:
    try:
        note = Note(content=content, profile_id=profile_id)
        session.add(note)
        session.commit()
        return note
    except Exception as e:
        logger.error(f"Error saving note: {e}")
        return None


def get_user_notes(session: Session, profile_id: uuid.UUID) -> List[Note]:
    notes = session.query(Note).filter(Note.profile_id == profile_id).all()

    return notes
