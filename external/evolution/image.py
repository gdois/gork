import httpx
import base64

from external.evolution.base import instance_name, evolution_api_key, evolution_api


async def send_sticker(contact_id: str, image_base64: str):
    url = f"{evolution_api}/message/sendSticker/{instance_name}"

    payload = {
        "number": contact_id,
        "sticker": image_base64
    }

    headers = {
        "Content-Type": "application/json",
        "apikey": evolution_api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60)
        return response.json()


async def download_image(message_id: str) -> bytes:
    media_url = f"{evolution_api}/chat/getBase64FromMediaMessage/{instance_name}"

    payload = {
        "message": {
            "key": {
                "id" :message_id,
            }
        },
        "convertToMp4": False
    }

    headers = {
        "Content-Type": "application/json",
        "apikey": evolution_api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(media_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        result = response.json()

        if 'base64' in result:
            return result['base64']