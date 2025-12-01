import httpx

from utils import get_env_var


def get_group_info(group_id: str) -> dict:
    evolution_api = get_env_var("EVOLUTION_API")
    evolution_api_key = get_env_var("API_KEY")
    instance_name = get_env_var("INSTANCE_NAME")

    headers = {
        "Content-Type": "application/json",
        "apikey": evolution_api_key,
    }

    req = httpx.get(f"{evolution_api}/group/findGroupInfos/{instance_name}?groupJid={group_id}", headers=headers)
    return req.json()