from datetime import datetime

import httpx

from log import openrouter_logger
from utils import get_env_var


OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"

async def make_request_openrouter(payload: dict) -> dict:
    start = datetime.now()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_env_var('OPENROUTER_KEY')}",
    }

    with httpx.Client(timeout=120) as client:
        response = client.post(f"{OPENROUTER_ENDPOINT}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        duration = datetime.now() - start
        minutes = duration.total_seconds() / 60
        await openrouter_logger.info("OpenRouter", "Request", f"Model: {payload.get('model')} - Time took: {minutes:.2f}")
        return response.json()
