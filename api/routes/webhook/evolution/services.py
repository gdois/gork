from apscheduler.schedulers.asyncio import AsyncIOScheduler

from api.routes.webhook.evolution.processors import process_group_message, process_private_message
from database import PgConnection
from log import logger


async def process_webhook(body: dict, scheduler: AsyncIOScheduler):
    async with PgConnection() as db:
        event_type = body.get("event")
        event_data = body.get("data")

        if event_type != "messages.upsert":
            return

        await logger.info("Request", body.get("instance"), body)

        remote_id = event_data.get("key", {}).get("remoteJid", "")
        alt_id = event_data.get("key", {}).get("remoteJidAlt", "")
        message_data = event_data.get("message", {})

        if remote_id.endswith(".net"):
            is_private = True
            phone_number = remote_id.replace("@s.whatsapp.net", "")
            remote_id = alt_id.replace("@lid", "")
        elif alt_id.endswith(".net"):
            is_private = True
            phone_number = alt_id.replace("@s.whatsapp.net", "")
            remote_id = remote_id.replace("@lid", "")
        elif remote_id.endswith("@g.us"):
            is_private = False

        if not is_private:
            await process_group_message(
                body, event_data, message_data, remote_id, db, scheduler
            )
        elif is_private:
            await process_private_message(
                body, event_data, message_data, remote_id, phone_number, db, scheduler
            )