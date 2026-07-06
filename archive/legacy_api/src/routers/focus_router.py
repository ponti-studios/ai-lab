from datetime import datetime
from typing import Annotated, Optional

import pytz
from fastapi import APIRouter, Query, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.orm import Query as SQQuery

from src.data.models.focus import (
    Focus,
    FocusItem,
    complete_focus,
    get_focus_by_id,
)
from src.utils.context import CurrentProfile, SessionDep
from src.utils.date_tools import get_end_of_day, get_start_of_day
from src.utils.logger import logger

focus_router = APIRouter()


def add_day_filter(query: SQQuery, timezone: str) -> SQQuery:
    # Get start and end of today in the client's timezone
    client_tz = pytz.timezone(timezone)
    start_of_today = get_start_of_day(client_tz)
    end_of_today = get_end_of_day(client_tz)

    # Convert to UTC for database query
    start_of_today_utc = start_of_today.astimezone(pytz.UTC)
    end_of_today_utc = end_of_today.astimezone(pytz.UTC)

    # Apply due date filter
    return query.filter(Focus.due_date >= start_of_today_utc).filter(Focus.due_date <= end_of_today_utc)


@focus_router.get("")
async def get_focus_items(
    profile: CurrentProfile,
    db: SessionDep,
    category: Optional[str] = None,
    timezone: str = Query(default="UTC", description="Timezone to use for date filtering"),
    start_date: Optional[str] = Query(
        default=get_start_of_day().strftime("%Y-%m-%d %H:%M:%S"),
        description="Return items after this datetime. Defaults to start of the current day.",
    ),
    end_date: Optional[str] = Query(
        default=get_end_of_day().strftime("%Y-%m-%d %H:%M:%S"),
        description="Return items before this datetime. Defaults to end of the current day.",
    ),
):
    print("start_date", start_date)
    print("end_date", end_date)
    query = db.query(Focus).filter(
        Focus.profile_id == profile.id,
        Focus.due_date.between(start_date, end_date),
    )

    # Apply category filter if provided
    if category:
        query = query.filter(Focus.category == category)

    # Apply ordering
    query = query.order_by(Focus.due_date.asc())

    # Execute query
    focus_items = query.all()
    for item in focus_items:
        if item.due_date:
            item.due_date = pytz.utc.localize(item.due_date).astimezone(pytz.timezone(timezone))

    return {"items": focus_items}


@focus_router.put("/complete/{task_id}", status_code=status.HTTP_200_OK)
async def complete_task(db: SessionDep, task_id: int):
    focus_item = get_focus_by_id(db, task_id)
    if not focus_item:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        focus_item = complete_focus(db, focus_item.id)
        return focus_item.to_json()
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail="Error updating task")


@focus_router.delete("/{id}")
async def delete_focus_item_route(id: int, db: SessionDep, profile: CurrentProfile) -> bool:
    note = db.query(Focus).filter(Focus.id == id).first()
    if not note:
        return False

    db.delete(note)
    db.commit()
    return True


class FocusUpdateInput(BaseModel):
    id: int
    text: Annotated[str, StringConstraints(min_length=1)]
    due_date: Annotated[Optional[datetime], Field(default=None, description="Due date for the focus item")]
    category: Annotated[Optional[str], Field(default=None, description="Category for the focus item")]
    timezone: Annotated[Optional[str], Field(default=None, description="Timezone for the focus item")]


@focus_router.put("/{id}")
async def update_focus_item_route(
    id: int, db: SessionDep, profile: CurrentProfile, input: FocusUpdateInput
) -> FocusItem:
    focus_item = get_focus_by_id(db, id)
    if not focus_item:
        raise HTTPException(status_code=404, detail="Focus item not found")

    focus_item.text = input.text
    if input.due_date and input.timezone:
        focus_item.due_date = input.due_date

    if input.category:
        focus_item.category = input.category

    db.commit()
    db.refresh(focus_item)
    return focus_item.to_model()
