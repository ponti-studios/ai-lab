import uuid
from datetime import datetime
from typing import Any, List, Optional, Tuple

import pydantic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.schema import AgentAction
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from typing_extensions import Dict, TypedDict

from src.data.chat_repository import get_chat_history
from src.data.db import SessionLocal
from src.data.focus_repository import create_focus_items
from src.data.models.focus import FocusItem, FocusItemBase, UserIntentTask
from src.services.file_service import get_file_contents
from src.services.openai_service import openai_chat
from src.services.user_intent.tools.search_tasks import (
    SearchIntentsResponse,
    format_search_tool_calls,
    search_tasks,
)


class IntentOutput(pydantic.BaseModel):
    function_name: str = pydantic.Field(description="The name of the function to call")
    parameters: Dict[str, Any] = pydantic.Field(description="The parameters to pass to the function")


@tool("task_record")
def task_record(
    profile_id: uuid.UUID,
    tasks: List[UserIntentTask],
) -> List[FocusItem]:
    """
    This tool is used to keep a record of actions the user has done or has to do in the future.

    Args:
        profile_id (uuid.UUID): The user's Profile ID
        tasks (List[FocusItemBase]): An array of tasks to be added to the list
    """
    session = SessionLocal()
    created_items = create_focus_items(focus_items=tasks, session=session, profile_id=profile_id)
    return [item.to_model() for item in created_items]


@tool("edit_task")
def edit_task(task_query: str, new_task_name: str, new_due_date: str, new_status: str) -> str:
    """
    Edit an existing task in a task list

    Args:
        task_query (str): The task query to search for the task to be edited
        new_task_name (str): The new name or description of the task
        new_due_date (str): The new due date in ISO Date Time Format for the task
        new_status (str): The updated status of the task
    """
    return "This feature is not yet implemented."


@tool("chat")
def start_chat(user_message: str) -> str:
    """
    This tool is used to begin a chat with the user.

    This should be used if the user says something that does not match any of the other tools.

    Args:
        user_message (str): The user's message
    """
    return user_message


class CreateTasksParameters(TypedDict):
    profile_id: uuid.UUID
    tasks: List[FocusItemBase]


class CreateIntentsResponse(pydantic.BaseModel):
    input: CreateTasksParameters
    output: List[FocusItem]


def format_create_tool_calls(intermediate_steps) -> CreateIntentsResponse | None:
    task_record: List[Tuple[AgentAction, List[FocusItem]]] = list(
        filter(lambda x: x[0].tool == "task_record", intermediate_steps)
    )

    if len(task_record) == 0:
        return None

    create_task = task_record[0]
    if create_task[0].tool_input is None:
        return None

    return CreateIntentsResponse(
        input={
            "tasks": create_task[0].tool_input["tasks"],  # type: ignore
            "profile_id": create_task[0].tool_input["profile_id"],  # type: ignore
        },
        output=task_record[0][1],
    )


class ChatParameters(TypedDict):
    user_message: str


class ChatResponse(pydantic.BaseModel):
    input: ChatParameters
    output: str


def format_chat_tool_call(intermediate_steps) -> ChatResponse | None:
    chat_calls: List[Tuple[AgentAction, str]] = list(
        filter(lambda x: x[0].tool == "chat", intermediate_steps)
    )

    if len(chat_calls) == 0:
        return None

    create_task = chat_calls[0]
    if create_task[0].tool_input is None:
        return None

    return ChatResponse(
        input=create_task[0].tool_input,  # type: ignore
        output=chat_calls[0][1],
    )


class GeneratedIntentsResponse(pydantic.BaseModel):
    input: str | None
    output: str | None
    chat: ChatResponse | None
    create: CreateIntentsResponse | None
    search: SearchIntentsResponse | None


def generate_intent_result(intent) -> GeneratedIntentsResponse:
    """
    Generates a response based on the user intent.

    Args:
        intent (dict): The user intent.

    Returns:
        result (GeneratedIntentsResponse): The generated response.
    """
    steps = intent["intermediate_steps"]
    output = intent["output"]
    search_output = format_search_tool_calls(steps)

    return GeneratedIntentsResponse(
        input=intent["user_input"],
        output=output,
        chat=format_chat_tool_call(steps),
        create=format_create_tool_calls(steps),
        search=search_output,
    )


def get_user_intent(
    session: Optional[Session], user_input: str, profile_id: uuid.UUID, chat_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    system_prompt = get_file_contents("src/services/user_intent/user_intent_prompt.md")
    tools = [task_record, search_tasks, edit_task, start_chat]
    chat_prompt = ChatPromptTemplate(
        [
            SystemMessagePromptTemplate.from_template(
                template=system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            HumanMessagePromptTemplate.from_template(
                "Profile ID: {profile_id} \n\n" + "Today's Date: {current_date} \n\n" + "{user_input}"
            ),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(openai_chat, tools, chat_prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
    )

    messages: List[HumanMessage | AIMessage] = []
    if chat_id and session:
        chat_history = get_chat_history(session, chat_id)
        for message in chat_history:
            if message.role == "user":
                messages.append(HumanMessage(content=message.message))
            elif message.role == "assistant":
                messages.append(AIMessage(content=message.message))

    result = agent_executor.invoke(
        {
            "profile_id": profile_id,
            "user_input": user_input,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "messages": messages,
        }
    )
    return result
