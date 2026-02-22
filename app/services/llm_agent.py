import httpx
import json
import asyncio
from app.core.config import get_settings
from app.data.prompt import IDENTIFICATION_PROMPT, CREATIVE_PROMPT, SUGGESTION_PROMPT
from app.core.exceptions import LLMApiError
from app.services.tmdb_service import search_media_data
from app.db import chat_history
from openai import AsyncAzureOpenAI
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

client = AsyncAzureOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
)

async def _call_llm_api(messages: list[dict], is_json: bool = False) -> str:
    try:
      response = await client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=messages,
        response_format={"type": "json_object"} if is_json else None,
        temperature=0.7,
      )

      return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in Azure OpenAI API: {e}")
        raise LLMApiError(detail=f"Error in Azure OpenAI API: {e}")

async def get_llm_response(db, chat_id: int, user_message: str) -> str:
    history_response = await chat_history.get_last_chats(db, chat_id)
    history = history_response.data

    identification_messages = [
        {"role": "system", "content": IDENTIFICATION_PROMPT},
    ]
    for entry in history:
        identification_messages.append({"role": "user", "content": entry.message})
        identification_messages.append({"role": "assistant", "content": entry.response})
    identification_messages.append({"role": "user", "content": user_message})

    identification_response_content = await _call_llm_api(identification_messages, is_json=True)
    try:
        media_list = json.loads(identification_response_content).get("media", [])
    except json.JSONDecodeError:
        media_list = []

    suggestion_response_content = ""
    if not media_list:
        suggestion_messages = [
            {"role": "system", "content": SUGGESTION_PROMPT},
        ]
        for entry in history:
            suggestion_messages.append({"role": "user", "content": entry.message})
            suggestion_messages.append({"role": "assistant", "content": entry.response})
        suggestion_messages.append({"role": "user", "content": user_message})

        suggestion_response_content = await _call_llm_api(suggestion_messages, is_json=True)
        try:
            suggested_media_list = json.loads(suggestion_response_content).get("media", [])
        except json.JSONDecodeError:
            suggested_media_list = []
        
        media_list = suggested_media_list

    if not media_list:
        creative_prompt_content = CREATIVE_PROMPT.format(
            user_query=user_message,
            media_data=json.dumps([], indent=2, ensure_ascii=False),
            identification_raw=identification_response_content,
            suggestion_raw=suggestion_response_content
        )
        creative_messages = [
            {"role": "system", "content": creative_prompt_content},
        ]
        for entry in history:
            creative_messages.append({"role": "user", "content": entry.message})
            creative_messages.append({"role": "assistant", "content": entry.response})
        creative_messages.append({"role": "user", "content": user_message})
        return await _call_llm_api(creative_messages)

    tasks = [search_media_data(
        media.get("type"), 
        media.get("title"), 
        media.get("year"), 
        media.get("actor"), 
        media.get("genre"),
        media.get("director")
    ) for media in media_list]
    media_data_results = await asyncio.gather(*tasks)

    formatted_media_data = []
    for media, data in zip(media_list, media_data_results):
        formatted_media_data.append({
            "title": media.get("title"),
            "type": media.get("type"),
            "year": media.get("year"),
            "trailer_link": data.get("trailer_link"),
            "poster_url": data.get("poster_url"),
            "watch_providers": data.get("watch_providers"),
            "cast": data.get("cast"),
            "raw_details_poster_path": data.get("raw_details_poster_path"),
            "raw_videos_results": data.get("raw_videos_results")
        })

    creative_prompt_content = CREATIVE_PROMPT.format(
        user_query=user_message,
        media_data=json.dumps(formatted_media_data, indent=2, ensure_ascii=False),
        identification_raw=identification_response_content,
        suggestion_raw=suggestion_response_content
    )
    creative_messages = [
        {"role": "system", "content": creative_prompt_content},
    ]
    for entry in history:
        creative_messages.append({"role": "user", "content": entry.message})
        creative_messages.append({"role": "assistant", "content": entry.response})
    creative_messages.append({"role": "user", "content": user_message})

    final_response = await _call_llm_api(creative_messages)

    return final_response.strip()