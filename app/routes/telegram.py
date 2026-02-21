from fastapi import APIRouter, Request, BackgroundTasks
import logging
from app.core.exceptions import JsonInvalidException
from app.bot.telegram import send_typing_action, send_message
from app.core.utils import validate_message, is_saludo, parse_message
from app.data.prompt import SALUDO_INICIAL
from app.db.chat_history import create_chat_history, get_last_chats, build_chat_context
from app.schemas.chat_history import ChatHistoryCreate, ChatHistoryListResponse
from app.db.database import AsyncSessionLocal
import asyncio
from app.services.llm_agent import get_llm_response

router = APIRouter(prefix="/telegram", 
                   tags=["telegram"], 
                   responses={404: {"description": "Not found"}})

logger = logging.getLogger(__name__)

async def process_message_task(chat_id: int, text: str):
    async with AsyncSessionLocal() as db:
        full_text = await build_chat_context(db, chat_id, text)
        
        async def keep_typing():
            while True:
                await send_typing_action(chat_id)
                await asyncio.sleep(4)

        typing_task = asyncio.create_task(keep_typing())
        try:
            response = await get_llm_response(db, chat_id, full_text)
            
            await create_chat_history(db, 
                                      ChatHistoryCreate(
                                          chat_id=chat_id,
                                          message=text, 
                                          response=response
                                      ))
            
            try:
                await send_message(chat_id, parse_message(response))
            except Exception as e:
                logger.error(f"Error sending formatted message (retrying plain text): {e}")
                await send_message(chat_id, response, parse_mode=None)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await send_message(chat_id, "Lo siento, ocurrió un error al procesar tu solicitud. Por favor intenta nuevamente.")
        finally:
            typing_task.cancel()

@router.get("/history/{chat_id}", response_model=ChatHistoryListResponse)
async def get_history(chat_id: int):
    async with AsyncSessionLocal() as db:
        return await get_last_chats(db, chat_id)

@router.post("/webhook/")
async def telegram_webhook(req: Request, background_tasks: BackgroundTasks):
    try:
        body = await req.json()
    except Exception:
        raise JsonInvalidException()
    
    message = body.get("message", {})
    chat_id, text = validate_message(message)

    if is_saludo(text):
        await send_message(chat_id, SALUDO_INICIAL)
    else:
        background_tasks.add_task(process_message_task, chat_id, text)

    return {"ok": True}