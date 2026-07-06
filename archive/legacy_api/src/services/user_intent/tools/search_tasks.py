import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import pydantic
from langchain.schema import AgentAction
from langchain_core.tools import tool

from src.data.focus_repository import search_focus_items
from src.data.models.focus import FocusItem, FocusState
from src.utils.date_tools import get_datetime_from_string


@tool("search_tasks", parse_docstring=True)
def search_tasks(
    keyword: str,
    search_title: str,
    profile_id: uuid.UUID,
    due_on: Optional[datetime | None] = None,
    due_after: Optional[datetime | None] = None,
    due_before: Optional[datetime | None] = None,
    status: Optional[FocusState | None] = None,
) -> List[FocusItem]:
    """
    Search for tasks based on a keyword or specific attributes.

    Args:
        keyword: The keyword to search for tasks
        search_title: A user-friendly title for the search
        profile_id: The user's Profile ID
        due_on: The due date in ISO Date Time Format for the task. Example: "2023-01-01T12:00" | None
        due_after: A ISO Date Time Format date used when the users wants to search for tasks after a specific date. Example: "2023-01-01T12:00" | None
        due_before: A ISO Date Time Format date used when the users wants to search for tasks before a specific date. Example: "2023-01-01T12:00" | None
        status: The status of the task
    """

    due_on = get_datetime_from_string(due_on)
    due_after = get_datetime_from_string(due_after)
    due_before = get_datetime_from_string(due_before)

    focus_items = search_focus_items(
        keyword=keyword,
        due_on=due_on,
        due_after=due_after,
        due_before=due_before,
        status=status,
        profile_id=profile_id,
    )

    return [focus_item.to_model() for focus_item in focus_items]


class SearchIntentParameters(pydantic.BaseModel):
    keyword: str
    profile_id: uuid.UUID
    due_on: Optional[datetime] | None = pydantic.Field(
        None, description="The due date in ISO Date Time Format for the task"
    )
    due_after: Optional[datetime] | None = pydantic.Field(
        None,
        description="A ISO Date Time Format date used when the users wants to search for tasks after a specific date",
    )
    due_before: Optional[datetime] | None = pydantic.Field(
        None,
        description="A ISO Date Time Format date used when the users wants to search for tasks before a specific date",
    )
    status: Optional[str] | None = pydantic.Field(None, description="The status of the task")


class SearchIntentsResponse(pydantic.BaseModel):
    input: SearchIntentParameters
    output: List[FocusItem]


def format_search_tool_calls(intermediate_steps) -> SearchIntentsResponse | None:
    search_tasks: List[Tuple[AgentAction, List[FocusItem]]] = list(
        filter(lambda x: x[0].tool == "search_tasks", intermediate_steps)
    )

    if len(search_tasks) == 0:
        return None

    search_task = search_tasks[0]
    if search_task[0].tool_input is None:
        return None

    return SearchIntentsResponse(
        input=search_task[0].tool_input,  # type: ignore
        output=search_tasks[0][1],
    )
