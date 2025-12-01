from typing import Optional

from database.models.manager import Agent
from database.operations import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    async def find_by_name(self, name: str) -> Optional[Agent]:
        return await self.find_one_by(name=name)

    async def upsert_by_name(self, name: str, prompt: str) -> Agent:
        """
        Insert or update an agent by name.
        If an agent with the given name exists, updates its prompt.
        Otherwise, creates a new agent.

        Args:
            name: The unique name of the agent
            prompt: The prompt text for the agent

        Returns:
            The created or updated Agent instance
        """
        existing_agent = await self.find_by_name(name)

        if existing_agent:
            return await self.update(existing_agent.id, {"prompt": prompt})
        else:
            new_agent = Agent(name=name, prompt=prompt)
            return await self.insert(new_agent)