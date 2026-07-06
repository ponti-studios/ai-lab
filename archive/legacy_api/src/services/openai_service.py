import uuid
from typing import List, Optional

from langchain.pydantic_v1 import BaseModel, SecretStr
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import AsyncOpenAI, OpenAI

from src.utils.config import settings

GPT4o = "gpt-4o-2024-08-06"
GPT4o_mini = "gpt-4o-mini"

OPENAI_API_KEY = settings.OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)

openai_async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

openai_chat = ChatOpenAI(model=GPT4o_mini, temperature=0.2, api_key=SecretStr(OPENAI_API_KEY))

openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


class ToolCall(BaseModel):
    input: str
    tool_calls: List[BaseModel]
    tool_outputs: Optional[List[str]] = None


def tool_example_to_messages(example: ToolCall) -> List[BaseMessage]:
    messages: List[BaseMessage] = [HumanMessage(content=example.input)]
    openai_tool_calls = [
        {
            "id": str(uuid.uuid4()),
            "type": "function",
            "function": {"name": tool_call.__class__.__name__, "arguments": tool_call.json()},
        }
        for tool_call in example.tool_calls
    ]

    messages.append(AIMessage(content="", additional_kwargs={"tool_calls": openai_tool_calls}))

    tool_outputs = example.tool_outputs or ["Tool called."] * len(openai_tool_calls)
    messages.extend(
        [
            ToolMessage(content=output, tool_call_id=tool_call["id"])
            for output, tool_call in zip(tool_outputs, openai_tool_calls)
        ]
    )

    return messages
