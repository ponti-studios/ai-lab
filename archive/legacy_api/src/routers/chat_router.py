import logging
import uuid
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic.main import BaseModel
from sqlalchemy.orm import Session

from src.data.chat_repository import insert_message
from src.data.models.chat import Chat, ChatState, Message, MessageOutput, MessageRole
from src.services.user_intent.user_intent_service import generate_intent_result, get_user_intent
from src.utils.context import CurrentProfile, CurrentUser, SessionDep

chat_router = APIRouter()


class ChatOutput(BaseModel):
    id: UUID
    title: str
    created_at: datetime


def get_active_chat(db: Session, profile_id: uuid.UUID) -> Chat | None:
    return (
        db.query(Chat)
        .filter(Chat.profile_id == profile_id)
        .filter(Chat.state == ChatState.ACTIVE.value)
        .order_by(Chat.created_at.desc())
        .first()
    )


class StartChatInput(BaseModel):
    user_message: str
    sherpa_message: str


@chat_router.post("/start")
async def start_chat(db: SessionDep, profile: CurrentProfile, input: StartChatInput) -> ChatOutput:
    chat = Chat(
        title="New Chat",
        profile_id=profile.id,
    )
    db.add(chat)
    db.commit()

    # Insert initial messages into the database
    insert_message(
        session=db,
        chat_id=chat.id,
        profile_id=profile.id,
        message=input.user_message,
        role=MessageRole.USER.value,
    )
    insert_message(
        session=db,
        chat_id=chat.id,
        profile_id=profile.id,
        message=input.sherpa_message,
        role=MessageRole.ASSISTANT.value,
    )

    return ChatOutput(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
    )


@chat_router.get("/active")
async def get_active_chat_route(
    db: SessionDep,
    profile: CurrentProfile,
) -> ChatOutput | None:
    try:
        chat = get_active_chat(db, profile.id)

        if chat is None:
            chat = Chat(
                title="New Chat",
                profile_id=profile.id,
            )
            db.add(chat)
            db.commit()
            db.flush()

        return ChatOutput(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
        )
    except (Exception, HTTPException) as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            logging.error(f"Error in get_active_chat: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")


class EndChatPayload(BaseModel):
    chat_id: UUID


@chat_router.post("/end")
async def end_chat(db: SessionDep, user: CurrentUser, input: EndChatPayload) -> ChatOutput | None:
    chat = db.query(Chat).filter(Chat.id == input.chat_id).first()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    chat.state = ChatState.ENDED.value
    db.add(chat)

    new_chat = Chat(
        title="New Chat",
        profile_id=chat.profile_id,
    )
    db.add(new_chat)
    db.commit()

    return ChatOutput(
        id=new_chat.id,
        title=new_chat.title,
        created_at=new_chat.created_at,
    )


@chat_router.get("/{chat_id}")
async def get_chat(db: SessionDep, user: CurrentUser, chat_id: UUID) -> list[MessageOutput] | None:
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    messages = db.query(Message).filter(Message.chat_id == chat_id).all()

    return [message.to_model(session=db) for message in messages]


class ChatMessageInput(BaseModel):
    message: str


class SendChatMessageOutput(BaseModel):
    messages: List[MessageOutput]
    function_calls: List[str]


@chat_router.post("/{chat_id}/messages")
async def send_chat_message(
    db: SessionDep, profile: CurrentProfile, input: ChatMessageInput, request: Request, chat_id: UUID
) -> SendChatMessageOutput:
    # Insert new message into the database
    user_message = insert_message(
        db, chat_id=chat_id, profile_id=profile.id, message=input.message, role="user"
    )

    # Retrieve message from ChatGPT
    user_intent = get_user_intent(
        session=db, user_input=input.message, profile_id=profile.id, chat_id=chat_id
    )
    sherpa_response = generate_intent_result(intent=user_intent)
    if sherpa_response is None:
        raise Exception("No response from the model")

    focus_items = []
    function_calls = []

    if sherpa_response.create is not None:
        focus_items.extend(sherpa_response.create.output)
        function_calls.append("task_record")

    if sherpa_response.search is not None:
        focus_items.extend(sherpa_response.search.output)
        function_calls.append("search_tasks")

    # Save assistant response to the database
    assistant_message = insert_message(
        db,
        chat_id=chat_id,
        profile_id=profile.id,
        role=MessageRole.ASSISTANT.value,
        message=sherpa_response.output or "",
        focus_ids=[item.id for item in focus_items],
    )

    return SendChatMessageOutput(
        messages=[
            user_message.to_model(session=db),
            assistant_message.to_model(session=db),
        ],
        function_calls=function_calls,
    )
