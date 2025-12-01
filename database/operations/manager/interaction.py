from typing import List, Optional

from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc, func as sql_func
from sqlalchemy.orm import joinedload

from database.models.manager import Interaction
from database.operations import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    async def find_by_command(self, command_id: int) -> List[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .options(joinedload(Interaction.model))
            .filter(Interaction.command_id == command_id)
            .order_by(Interaction.inserted_at)
        )
        return list(result.unique().scalars().all())

    async def find_by_model(self, model_id: int, limit: int = 100) -> List[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .filter(Interaction.model_id == model_id)
            .order_by(desc(Interaction.inserted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_agent(self, agent_id: int, limit: int = 100) -> List[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .filter(Interaction.agent_id == agent_id)
            .order_by(desc(Interaction.inserted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_conversation_history(
            self,
            command_id: int,
            include_model: bool = True,
            include_agent: bool = False
    ) -> List[Interaction]:
        query = select(Interaction).filter(Interaction.command_id == command_id)

        options = []
        if include_model:
            options.append(joinedload(Interaction.model))
        if include_agent:
            options.append(joinedload(Interaction.agent))

        if options:
            query = query.options(*options)

        query = query.order_by(Interaction.inserted_at)

        result = await self.db.execute(query)
        return list(result.unique().scalars().all() if options else result.scalars().all())

    async def create_interaction(
            self,
            model_id: int,
            sender: str,
            content: str,
            tokens: int,
            command_id: Optional[int] = None,
            agent_id: Optional[int] = None,
            interaction_id: Optional[int] = None
    ) -> Interaction:
        if sender not in ['user', 'assistant']:
            raise ValueError("sender must be 'user' or 'assistant'")

        interaction = Interaction(
            model_id=model_id,
            sender=sender,
            command_id=command_id,
            agent_id=agent_id,
            interaction_id=interaction_id,
            content=content,
            tokens=tokens
        )
        return await self.insert(interaction)

    async def get_total_tokens_by_command(self, command_id: int) -> int:
        result = await self.db.execute(
            select(sql_func.sum(Interaction.tokens))
            .filter(Interaction.command_id == command_id)
        )
        total = result.scalar_one_or_none()
        return total if total else 0

    async def get_total_tokens_by_agent(
            self,
            agent_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> int:
        filters = [Interaction.agent_id == agent_id]

        if start_date:
            filters.append(Interaction.inserted_at >= start_date)
        if end_date:
            filters.append(Interaction.inserted_at <= end_date)

        result = await self.db.execute(
            select(sql_func.sum(Interaction.tokens))
            .filter(and_(*filters))
        )
        total = result.scalar_one_or_none()
        return total if total else 0

    async def get_total_tokens_by_model(
            self,
            model_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> int:
        filters = [Interaction.model_id == model_id]

        if start_date:
            filters.append(Interaction.inserted_at >= start_date)
        if end_date:
            filters.append(Interaction.inserted_at <= end_date)

        result = await self.db.execute(
            select(sql_func.sum(Interaction.tokens))
            .filter(and_(*filters))
        )
        total = result.scalar_one_or_none()
        return total if total else 0

    async def get_interactions_count(
            self,
            model_id: Optional[int] = None,
            agent_id: Optional[int] = None,
            sender: Optional[str] = None,
            hours: Optional[int] = None
    ) -> int:
        filters = []

        if model_id:
            filters.append(Interaction.model_id == model_id)
        if agent_id:
            filters.append(Interaction.agent_id == agent_id)
        if sender:
            filters.append(Interaction.sender == sender)
        if hours:
            time_threshold = datetime.now() - timedelta(hours=hours)
            filters.append(Interaction.inserted_at >= time_threshold)

        result = await self.db.execute(
            select(sql_func.count(Interaction.id))
            .filter(and_(*filters) if filters else True)
        )
        return result.scalar_one()

    async def get_recent_interactions(
            self,
            hours: int = 24,
            limit: int = 50,
            include_agent: bool = False
    ) -> List[Interaction]:
        time_threshold = datetime.now() - timedelta(hours=hours)

        options = [
            joinedload(Interaction.model),
            joinedload(Interaction.command)
        ]
        if include_agent:
            options.append(joinedload(Interaction.agent))

        result = await self.db.execute(
            select(Interaction)
            .options(*options)
            .filter(Interaction.inserted_at >= time_threshold)
            .order_by(desc(Interaction.inserted_at))
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def get_child_interactions(self, parent_interaction_id: int) -> List[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .filter(Interaction.interaction_id == parent_interaction_id)
            .order_by(Interaction.inserted_at)
        )
        return list(result.scalars().all())

    async def calculate_cost(
            self,
            command_id: Optional[int] = None,
            model_id: Optional[int] = None,
            agent_id: Optional[int] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> dict:
        filters = []
        if command_id:
            filters.append(Interaction.command_id == command_id)
        if model_id:
            filters.append(Interaction.model_id == model_id)
        if agent_id:
            filters.append(Interaction.agent_id == agent_id)
        if start_date:
            filters.append(Interaction.inserted_at >= start_date)
        if end_date:
            filters.append(Interaction.inserted_at <= end_date)

        result = await self.db.execute(
            select(
                Interaction.sender,
                sql_func.sum(Interaction.tokens).label('total_tokens')
            )
            .filter(and_(*filters) if filters else True)
            .group_by(Interaction.sender)
        )

        token_stats = {row.sender: row.total_tokens for row in result.all()}

        return {
            "user_tokens": token_stats.get('user', 0),
            "assistant_tokens": token_stats.get('assistant', 0),
            "total_tokens": sum(token_stats.values())
        }