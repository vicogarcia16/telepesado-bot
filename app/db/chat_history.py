from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import (
    ChatHistoryCreate,
    ChatHistoryResponse,
    ChatHistoryListResponse,
)
from sqlalchemy import select, desc, asc
from sqlalchemy.orm import aliased
from app.core.utils import clean_text

async def get_last_chats(db: AsyncSession, chat_id: int, limit: int = 5):
    subquery = (
        select(ChatHistory)
        .where(ChatHistory.chat_id == chat_id)
        .order_by(desc(ChatHistory.created_at))
        .limit(limit)
        .subquery()
    )

    aliased_chat = aliased(ChatHistory, subquery)

    result = await db.execute(
        select(aliased_chat).order_by(asc(aliased_chat.created_at))
    )
        
    chat_history = result.scalars().all()
    if not chat_history:
        return ChatHistoryListResponse(message="No chat history found", data=[])

    return ChatHistoryListResponse(message="Chat history found", data=chat_history)

async def create_chat_history(db: AsyncSession, chat_history: ChatHistoryCreate):
    db_chat_history = ChatHistory(**chat_history.model_dump())
    db.add(db_chat_history)
    await db.commit()
    await db.refresh(db_chat_history)
    return ChatHistoryResponse(message="Chat history created", data=db_chat_history)

async def build_chat_context(db: AsyncSession, chat_id: int, user_message: str) -> str:
    last_chats = await get_last_chats(db, chat_id)
    context = "\n".join(
        f"User: {clean_text(chat.message)}\nBot: {clean_text(chat.response)}"
        for chat in reversed(last_chats.data)
    )
    return f"{context}\nUser: {user_message}" if context else f"User: {user_message}"
