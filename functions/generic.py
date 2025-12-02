import json
from datetime import datetime
from uuid import uuid4

from database import PgConnection
from database.models.base import User
from database.models.content import Message
from database.operations.base.user import UserRepository
from database.operations.content.message import MessageRepository
from services import manage_interaction


async def generic_conversation(group_id: int, user_name: str, last_message: str) -> dict:

    async with PgConnection() as db:
        user_repo = UserRepository(User, db)
        user_gork = await user_repo.find_by_name("Gork")

        message_repo = MessageRepository(Message, db)
        messages = await message_repo.find_by_group(group_id, 20)

        formatted_messages = []
        existing_messages = []
        for msg in messages:
            sender_name = msg.sender.name or msg.sender.phone_jid or "Usuário Desconhecido"
            content = msg.content or ""

            if content.lower() in existing_messages:
                continue

            msg_date = msg.created_at.date()
            today = datetime.now().date()

            if msg_date != today:
                timestamp = msg.created_at.strftime('%d/%m/%Y %H:%M')
            else:
                timestamp = msg.created_at.strftime('%H:%M')

            formatted_messages.append(f"{sender_name}: {content} - {timestamp}")
            existing_messages.append(content.lower())

        formatted_messages.append(f"""
        \nUltima mensagem enviada e que dever ser respondida: 
        {user_name}: {last_message} - {datetime.now().strftime('%H:%M')}
        """)

        final_message = "\n".join(formatted_messages)

        resp = await manage_interaction(db, final_message, agent_name="generic")

        _ = await message_repo.insert(Message(
            message_id=str(uuid4()),
            group_id = group_id,
            sender_id=user_gork.id,
            content=resp,
            created_at=datetime.now()
        ))

        return json.loads(f"""{resp}""")