import httpx
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

async def send_typing_action(chat_id: int) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{settings.api_telegram}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })
        response.raise_for_status()

async def send_message(chat_id: int, text: str, parse_mode: str | None = "HTML") -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
            
        response = await client.post(f"{settings.api_telegram}/sendMessage", json=payload)
        
        if response.status_code != 200:
            logger.error(f"Telegram API Error: {response.text}")
            
        response.raise_for_status()
