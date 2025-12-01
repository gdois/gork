import os

from database import PgConnection
from database.models.manager import Agent
from database.operations.manager import AgentRepository
from log import logger
from utils import project_root


async def init_agents() -> None:
    files = os.listdir(f"{project_root}/agents")
    md_files = [file for file in files if file.endswith(".md")]
    async with PgConnection() as db:
        agent_repo = AgentRepository(Agent, db)

        for file in md_files:
            agent_name = file.split(".")[0]

            with open(f"{project_root}/agents/{file}", "r", encoding="utf-8") as f:
                content = f.read()

            _ = await agent_repo.upsert_by_name(
                name = agent_name,
                prompt = content
            )

    await logger.info("Agents", "Initialization", "Successful")

    return