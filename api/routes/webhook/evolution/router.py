from fastapi import APIRouter, Request, HTTPException
from starlette import status
import asyncio

from scheduler import scheduler
from api.routes.webhook.evolution.services import process_webhook
from log import logger
from utils import get_env_var


router = APIRouter(
    prefix="/webhook/evolution",
    tags=["Webhook", "Evolution", "WhatsApp Events"]
)

EVOLUTION_INSTANCE_KEY = get_env_var("EVOLUTION_INSTANCE_KEY")


@router.post("")
async def evolution_webhook(request: Request):
    try:
        body = await request.json()
    except Exception as e:
        await logger.error("Webhook", "Error reading body", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )

    api_key = body.get("apikey")
    if api_key != EVOLUTION_INSTANCE_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    asyncio.create_task(process_webhook(body, scheduler))

    return {"status": "received"}
