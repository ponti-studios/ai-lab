import traceback
import uuid
from datetime import datetime
from typing import List, Optional

from langchain_core.documents import Document
from sqlalchemy.orm import Session

from src.data.db import SessionLocal
from src.data.models.focus import Focus, FocusState, UserIntentTask
from src.services import chroma_service
from src.utils.logger import logger

NON_TASK_TYPES = ["chat", "feeling", "request", "question"]


def get_focus_vector_documents(
    focus_items: List[Focus], base_items: Optional[List[UserIntentTask]] = None
) -> List[Document]:
    documents: List[Document] = []

    for item in focus_items:
        if base_items:
            keywords = next(base_item for base_item in base_items if base_item.text == item.text).keywords
            keywords_str = ",".join(keywords)
        else:
            keywords_str = ""

        documents.append(
            Document(
                page_content=f"{item.text} \n\n {keywords_str}",
                metadata=item.to_json(),
            )
        )

    return documents


def get_focus_item_by_id(focus_items: List[Focus], id: str) -> Focus:
    focus_item = next((item for item in focus_items if str(item.id) == id), None)
    return focus_item


def add_focus_items_to_vector_store(
    focus_items: List[Focus], base_items: List[UserIntentTask]
) -> List[Focus] | None:
    try:
        documents = get_focus_vector_documents(focus_items, base_items)
        logger.info(f"Adding {len(documents)} focus items to vector store...")
        uuids = [item.metadata["id"] for item in documents]
        ids = chroma_service.vector_store.add_documents(documents=documents, ids=uuids)
        logger.info(f"Added focus {len(ids)} items to vector store:", {"ids": ids})

        for item in focus_items:
            item.in_vector_store = True

        return focus_items
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error adding documents to Chroma: {e}")
        return None


def delete_focus_item_from_vector_store(focus_item: Focus):
    if not focus_item.in_vector_store:
        return

    try:
        logger.info(f"Deleting {focus_item.id} from vector store...")
        chroma_service.vector_store.delete(ids=[str(focus_item.id)])
        focus_item.in_vector_store = False
        logger.info(f"Deleted {focus_item.id} from vector store.")
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error deleting {focus_item.text} from vector store: {e}")
        return None


def create_focus_items(
    focus_items: List[UserIntentTask], profile_id: uuid.UUID, session: Session
) -> List[Focus]:
    filtered_items = [item for item in focus_items if item.type not in NON_TASK_TYPES]
    if len(filtered_items) == 0:
        return []

    created_items = [
        Focus(
            text=item.text,
            type=item.type,
            task_size=item.task_size,
            category=item.category,
            priority=item.priority,
            sentiment=item.sentiment,
            due_date=item.due_date,
            profile_id=profile_id,
            state=item.state.value,
        )
        for item in focus_items
    ]

    session.add_all(created_items)
    session.flush()
    session.commit()

    add_focus_items_to_vector_store(focus_items=created_items, base_items=focus_items)

    return created_items


def search_focus_items(
    keyword: str,
    due_on: Optional[datetime],
    due_after: Optional[datetime],
    due_before: Optional[datetime],
    status: Optional[FocusState],
    profile_id: uuid.UUID,
) -> List[Focus]:
    session = SessionLocal()
    ids = []

    if len(keyword) > 0:
        results = chroma_service.vector_store.similarity_search_with_relevance_scores(
            query=keyword,
            filter={"profile_id": str(profile_id)},
            score_threshold=0,
        )
        ids = []
        for res, score in results:
            logger.info(f"Found {res.metadata['text']} with score {score}")
            ids.append(res.metadata["id"])
        if len(ids) == 0:
            return []

    try:
        query = session.query(Focus).filter(Focus.profile_id == profile_id)

        if len(ids) > 0:
            query = query.filter(Focus.id.in_(ids))

        if due_on:
            query = query.filter(Focus.due_date == due_on)
        else:
            # `due_after` and `due_before` can be used together because
            # the user may want to search for tasks that are due between two dates
            if due_after is not None:
                query = query.filter(Focus.due_date >= due_after)

            if due_before is not None:
                query = query.filter(Focus.due_date <= due_before)

        if status == "active" or status == FocusState.backlog.value:
            query = query.filter(Focus.state.in_([FocusState.backlog.value, FocusState.active.value]))
        elif status:
            query = query.filter(Focus.state == status.value)

        focus_items = query.limit(10).all()

        return focus_items
    except Exception as e:
        logger.error(f"Error searching focus items: {e}")
        return []
