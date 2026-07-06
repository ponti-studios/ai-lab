import uuid
from datetime import datetime
from typing import Annotated, List

import pydantic
from langchain.agents import create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langgraph.graph import END, Graph
from typing_extensions import TypedDict

from src.routers.chat_router import start_chat
from src.services.file_service import get_file_contents
from src.services.openai_service import openai_chat
from src.services.user_intent.tools import search_tasks
from src.services.user_intent.tools.search_tasks import format_search_tool_calls
from src.services.user_intent.user_intent_service import (
    GeneratedIntentsResponse,
    edit_task,
    format_chat_tool_call,
    format_create_tool_calls,
    task_record,
)


class AgentState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], pydantic.Field(default_factory=list)]
    tools_used: Annotated[list[str], pydantic.Field(default_factory=list)]
    tool_to_use: str
    profile_id: uuid.UUID
    current_date: str


def determine_tool(state: AgentState):
    system_prompt = get_file_contents("src/services/user_intent/user_intent_prompt.md")
    tools = [task_record, search_tasks, edit_task, start_chat]
    chat_prompt = ChatPromptTemplate(
        [
            SystemMessagePromptTemplate.from_template(template=system_prompt),
            ("human", ("Profile ID: {profile_id} \n\n" + "Today's Date: {current_date} \n\n" + "{input}")),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(openai_chat, tools, chat_prompt)
    result = agent.invoke(state)
    tool_to_use = result.tool
    return tool_to_use


def execute_tool(state: AgentState):
    tool_name = state["tool_to_use"]
    tools = {
        "task_record": task_record,
        "search_tasks": search_tasks,
        "edit_task": edit_task,
        "chat": start_chat,
    }
    tool = tools[tool_name]
    result = tool(**state)  # You might need to adjust this based on your tool implementations
    state["tools_used"].append(tool_name)
    state["messages"].append(AIMessage(content=str(result)))
    return state


def should_continue(state: AgentState):
    # For simplicity, let's say we continue if we've used less than 3 tools
    return len(state["tools_used"]) < 3


workflow = Graph()

workflow.add_node("determine_tool", determine_tool)
workflow.add_node("execute_tool", execute_tool)

workflow.add_edge("determine_tool", "execute_tool")
workflow.add_conditional_edges("execute_tool", should_continue, {True: "determine_tool", False: END})

workflow.set_entry_point("determine_tool")

chain = workflow.compile()


def get_user_intent_graph(user_input: str, profile_id: uuid.UUID) -> AgentState:
    initial_state = AgentState(
        messages=[HumanMessage(content=user_input)],
        tool_to_use="",
        tools_used=[],
        profile_id=profile_id,
        current_date=datetime.now().strftime("%Y-%m-%d"),
    )
    result = chain.invoke(initial_state)
    result = AgentState(**result)
    return result


def generate_intent_result_graph(intent: AgentState) -> GeneratedIntentsResponse:
    """
    Generates a response based on the user intent.

    Args:
        intent (AgentState): The final state after running the workflow.

    Returns:
        result (GeneratedIntentsResponse): The generated response.
    """
    steps = intent["tools_used"]
    output = intent["messages"][-1].content if intent["messages"] else ""
    first_message = intent["messages"][0].content

    return GeneratedIntentsResponse(
        input=first_message if isinstance(first_message, str) else None,
        output=output if isinstance(output, str) else None,
        chat=format_chat_tool_call(steps),
        create=format_create_tool_calls(steps),
        search=format_search_tool_calls(steps),
    )
