from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, and_, desc

from database.models.content import Media
from database.operations import BaseRepository


class MediaRepository(BaseRepository[Media]):

    async def find_by_message(self, message_id: int, limit: int = 50) -> List[Media]:
        result = await self.db.execute(
            select(Media)
            .filter(
                and_(
                    Media.message_id == message_id,
                    Media.deleted_at.is_(None)
                )
            )
            .order_by(desc(Media.inserted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_user(self, user_id: int, limit: int = 50) -> List[Media]:
        result = await self.db.execute(
            select(Media)
            .filter(
                and_(
                    Media.user_id == user_id,
                    Media.deleted_at.is_(None)
                )
            )
            .order_by(desc(Media.inserted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_type(self, media_type: str, limit: int = 50) -> List[Media]:
        result = await self.db.execute(
            select(Media)
            .filter(
                and_(
                    Media.type == media_type,
                    Media.deleted_at.is_(None)
                )
            )
            .order_by(desc(Media.inserted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_recent_media(
            self,
            minutes: int = 5,
            user_id: Optional[int] = None,
            media_type: Optional[str] = None
    ) -> List[Media]:
        from datetime import timedelta
        time_threshold = datetime.now() - timedelta(minutes=minutes)

        filters = [
            Media.inserted_at >= time_threshold,
            Media.deleted_at.is_(None)
        ]

        if user_id:
            filters.append(Media.user_id == user_id)
        if media_type:
            filters.append(Media.type == media_type)

        result = await self.db.execute(
            select(Media)
            .filter(and_(*filters))
            .order_by(desc(Media.inserted_at))
        )
        return list(result.scalars().all())

    async def semantic_search(
            self,
            query_embedding: List[float],
            media_type: Optional[str] = None,
            user_id: Optional[int] = None,
            limit: int = 10
    ) -> List[dict]:
        query = select(
            Media,
            Media.embedding.cosine_distance(query_embedding).label('distance')
        ).filter(Media.deleted_at.is_(None))

        if media_type:
            query = query.filter(Media.type == media_type)
        if user_id:
            query = query.filter(Media.user_id == user_id)

        query = query.order_by('distance').limit(limit)
        result = await self.db.execute(query)

        return [
            {
                "id": row.Media.id,
                "name": row.Media.name,
                "bucket": row.Media.bucket,
                "sub_path": row.Media.sub_path,
                "type": row.Media.type,
                "similarity": 1 - float(row.distance)
            }
            for row in result.all()
        ]

    async def soft_delete(self, media_id: int) -> bool:
        """Soft delete de mídia."""
        media = await self.find_by_id(media_id)
        if not media:
            return False

        return await self.update(media.id, {"deleted_at": datetime.now()}) is not None

    async def count_by_user(self, user_id: int) -> int:
        """Conta mídias de um usuário."""
        from sqlalchemy import func as sql_func
        result = await self.db.execute(
            select(sql_func.count(Media.id))
            .filter(
                and_(
                    Media.user_id == user_id,
                    Media.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def count_by_type(self, media_type: str) -> int:
        """Conta mídias por tipo."""
        from sqlalchemy import func as sql_func
        result = await self.db.execute(
            select(sql_func.count(Media.id))
            .filter(
                and_(
                    Media.type == media_type,
                    Media.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()