from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from src.data.models.focus import Focus


def send_push_notification(push_token, message):
    headers = {
        "Authorization": "Bearer YOUR_EXPO_ACCESS_TOKEN",
        "Content-Type": "application/json",
    }

    payload = {"to": push_token, "sound": "default", "body": message, "data": {"extra": "data"}}

    response = requests.post("https://exp.host/--/api/v2/push/send", json=payload, headers=headers)
    return response.status_code


def notify_due_tasks(db: Session):
    now = datetime.now(timezone.utc)
    upcoming_tasks = db.query(Focus).filter(Focus.due_date <= now + timedelta(hours=1)).all()

    for task in upcoming_tasks:
        # Assume the task object has a `user.push_token`
        send_push_notification(task.user.push_token, f"Task '{task.name}' is due soon!")
