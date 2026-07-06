import pytest

from src.utils.logger import logger


def test_get_active_chat(client, db_session, profile, auth_headers, user, active_chat):
    logger.info(f"User ID: {user.id} {user.email}")
    response = client.get("/chat/active", headers=auth_headers)
    chat = response.json()
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert chat["title"] == "Test Chat"


# def test_get_active_chat_not_found(client, db_session, profile, auth_headers):
#     # Ensure there are no active chats
#     db_session.query(Chat).filter(
#         Chat.profile_id == profile.id, Chat.state == ChatState.ACTIVE.value
#     ).delete()
#     db_session.commit()

#     response = client.get("/chat/active", headers=auth_headers)
#     assert response.status_code == 500
#     assert "Internal server error" in response.json()["detail"]


# def test_end_chat(client, active_chat, auth_headers, db_session):
#     response = client.post("/chat/end", json={"chat_id": str(active_chat.id)}, headers=auth_headers)
#     assert response.status_code == 200
#     assert isinstance(response.json(), dict)

#     db_session.refresh(active_chat)
#     assert active_chat.state == ChatState.ENDED.value


# def test_end_chat_not_found(client, auth_headers):
#     non_existent_chat_id = uuid.uuid4()
#     response = client.post("/chat/end", json={"chat_id": str(non_existent_chat_id)}, headers=auth_headers)
#     assert response.status_code == 500
#     assert "Internal server error" in response.json()["detail"]


# def test_get_chat(client, active_chat, auth_headers, db_session, profile):
#     for _ in range(3):
#         message = Message(
#             chat_id=active_chat.id, message="Test message", role=MessageRole.USER.value, profile_id=profile.id
#         )
#         db_session.add(message)
#     db_session.commit()

#     response = client.get(f"/chat/{active_chat.id}", headers=auth_headers)
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert len(response.json()) == 3


# def test_get_chat_not_found(client, auth_headers):
#     non_existent_chat_id = uuid.uuid4()
#     response = client.get(f"/chat/{non_existent_chat_id}", headers=auth_headers)
#     assert response.status_code == 500
#     assert "Internal server error" in response.json()["detail"]


# def test_unauthorized_access(client):
#     endpoints = ["/chat/active", "/chat/end", f"/chat/{uuid.uuid4()}"]
#     for endpoint in endpoints:
#         response = client.get(endpoint)
#         assert response.status_code == 401
#         assert "Unauthorized" in response.json()["detail"]
