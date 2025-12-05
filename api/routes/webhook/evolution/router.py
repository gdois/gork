from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from starlette import status

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
async def evolution_webhook(
        request: Request,
        background_tasks: BackgroundTasks
):
    try:
        body = await request.json()
    except Exception as e:
        await logger.error("Webhook", "Error reading body", str(e))
        return {"status": "error"}

    api_key = body.get("apikey")

    if api_key != EVOLUTION_INSTANCE_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    background_tasks.add_task(process_webhook, body, scheduler)

    return {"status": "received"}