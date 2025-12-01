import httpx

from external.evolution.base import evolution_api, evolution_api_key, instance_name


async def send_message(contact_id: str, message: str, message_id: str ):
    url = f"{evolution_api}/message/sendText/{instance_name}"

    payload = {
        "number": contact_id,
        "text": message,
        "quoted": {
            "key": {"id": message_id},
        }
    }

    headers = {
        "Content-Type": "application/json",
        "apikey": evolution_api_key
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=60)
        return response.json()