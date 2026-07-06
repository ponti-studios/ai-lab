import uuid
from typing import List, Optional

from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.orm import Session

from src.data.models.user import User
from src.data.users_repository import get_user_context
from src.services.openai_service import openai_chat
from src.services.prompt_service import AvailablePrompts, get_prompt
from src.utils.logger import logger


class SherpaResponseMetadata(BaseModel):
    user_query_category: str
    related_context_items: List[str] = Field(
        default_factory=list,
        description="List of User Context items that are related to the user query.",
    )


class SherpaResponse(BaseModel):
    message: str
    metadata: Optional[SherpaResponseMetadata] = None


def get_chat_response(session: Session, message: str, profile_id: uuid.UUID, user: User) -> SherpaResponse:
    try:
        system_prompt = get_prompt(AvailablePrompts.SherpaChatResponse)
        user_context = get_user_context(session, profile_id=profile_id)

        parser = JsonOutputParser(pydantic_object=SherpaResponse)
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    template=system_prompt,
                    partial_variables={
                        "format_instructions": parser.get_format_instructions(),
                        "user_context": f"User's name: {user.name}\n\n" + "\n".join(user_context.focus_items),
                    },
                ),
                ChatPromptTemplate.from_messages(
                    [HumanMessage(content=message) for message in user_context.chat_history]
                ),
                ("human", "{user_input}"),
            ]
        )

        chain = {"user_input": RunnablePassthrough()} | prompt | openai_chat

        llm_response = chain.invoke({"user_input": message})

        if isinstance(llm_response.content, str):
            try:
                parsed = parser.parse(llm_response.content)
                return SherpaResponse(message=parsed["message"], metadata=parsed["metadata"])
            except Exception:
                return SherpaResponse(message=llm_response.content)
        else:
            raise Exception("LLM Response is not a string")
    except Exception as e:
        logger.error(f"Generating sherpa response: {e}")
        raise e
