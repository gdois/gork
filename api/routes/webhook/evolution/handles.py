import re
from datetime import datetime, timedelta
from typing import Optional
from textwrap import dedent

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.manager import Model
from database.operations.manager import ModelRepository
from functions import get_resume_conversation, generic_conversation, generate_sticker, remember_generator, generate_image
from functions.transcribe_audio import transcribe_audio
from functions.web_search import web_search
from external.evolution import send_message, send_audio, send_sticker, send_image
from services.remember import action_remember
from tts import text_to_speech


COMMANDS = [
    ("@Gork", "Interação genérica. _[Menção necessária apenas quando em grupos]_"),
    ("!help", "Mostra os comandos disponíveis. _[Ignora o restante da mensagem]_"),
    ("!audio", "Envia áudio como forma de resposta. _[Adicione !english para voz em inglês]_"),
    ("!resume", "Faz um resumo das últimas 30 mensagens. _[Ignora o restante da mensagem]_"),
    ("!search", "Faz uma pesquisa por termo na internet e retorna um resumo."),
    ("!model", "Mostra o modelo sendo utilizado."),
    ("!sticker", "Cria um sticker com base em uma imagem e texto fornecido. _[Use | como separador de top/bottom]_"),
    ("!english", ""),
    ("!remember",
     "Cria um lembrete para o dia, hora e tópico solicitado. _[Ex: Lembrete para comentar amanhã as 4 da tarde]_"),
    ("!transcribe", "Transcreve um áudio. _[Ignora o restante da mensagem]_"),
    ("!image", "Gera ou modifica uma imagem mencionada.")
]


async def extract_conversation_text(message_data: dict) -> str:
    caption = message_data.get('imageMessage', {}).get('caption', '')
    conversation = caption if caption else message_data.get("conversation", "")

    if not conversation:
        conversation = (
            message_data.get("ephemeralMessage", {})
            .get("message", {})
            .get("extendedTextMessage", {})
            .get("text", "")
        )

    return conversation


async def is_message_too_old(timestamp: int, max_minutes: int = 20) -> bool:
    created_at = datetime.fromtimestamp(timestamp)
    return created_at < (datetime.now() - timedelta(minutes=max_minutes))


def clean_text(text: str) -> str:
    treated_text = text.strip()
    for command, _ in COMMANDS:
        treated_text = treated_text.replace(command, "")

    treated_text = re.compile(r'@\d{6,15}').sub('', treated_text)
    return treated_text.strip()


async def handle_help_command(remote_id: str, message_id: str):
    tt_messages = ["*Comandos do Gork disponíveis.*"]
    for command, desc in COMMANDS:
        if desc:
            tt_messages.append(f"*{command}* - {desc}\n")

    tt_messages.append(dedent("""
       💡 *Dica: Fale naturalmente com o Gork!*
        Você não precisa digitar comandos. Apenas fale normalmente:
        - "me avisa amanhã às 10h" → cria lembrete
        - "pesquisa sobre Python" → busca na internet
        - "cria uma imagem de gato espacial" → gera imagem
        - "resume a conversa" → faz resumo

        Comandos como !remember, !search são mais rápidos, precisos e econômicos, mas *totalmente opcionais*.
    """))
    tt_commands = "\n".join(tt_messages)
    final_message = f"{tt_commands}\nContribute on https://github.com/pedrohgoncalvess/gork"
    await send_message(remote_id, final_message, message_id)


async def handle_model_command(remote_id: str, message_id: str, db: AsyncSession):
    model_repo = ModelRepository(Model, db)
    model = await model_repo.get_default_model()
    audio_model = await model_repo.get_default_audio_model()
    image_model = await model_repo.get_default_image_model()

    formatted_text = (
        f"*Modelos sendo utilizados*:\n\n"
        f"Texto: _{model.name}_\n"
        f"Áudio: _{audio_model.name}_\n"
        f"Imagem: _{image_model.name}_"
    )
    await send_message(remote_id, formatted_text, message_id)


async def handle_resume_command(
        remote_id: str,
        message_id: str,
        user_id: int,
        group_id: Optional[int] = None
):
    resume = await get_resume_conversation(user_id, group_id=group_id)
    await send_message(remote_id, resume, message_id)


async def handle_search_command(
        remote_id: str,
        message_id: str,
        treated_text: str,
        group: bool
):
    search = await web_search(treated_text, remote_id, group)
    await send_message(remote_id, search, message_id)


async def handle_image_command(
        remote_id: str,
        user_id: int,
        treated_text: str,
        body: dict,
        group_id: Optional[int] = None
):
    image_base64, error = await generate_image(user_id, treated_text, body, group_id)
    if error:
        await send_message(remote_id, image_base64)
        return
    await send_image(remote_id, image_base64)
    return


async def handle_sticker_command(
        remote_id: str,
        body: dict,
        treated_text: str
):
    webp_base64 = await generate_sticker(body, treated_text)
    await send_sticker(remote_id, webp_base64)


async def handle_transcribe_command(
        remote_id: str,
        message_id: str,
        body: dict
):
    transcribed_audio = await transcribe_audio(body)
    transcribed_audio = f"_{transcribed_audio.strip()}_"
    await send_message(remote_id, transcribed_audio, message_id)


async def handle_remember_command(
        scheduler: AsyncIOScheduler,
        remote_id: str,
        message_id: str,
        user_id: int,
        treated_text: str,
        group_id: Optional[int] = None
):
    remember, feedback_message = await remember_generator(user_id, treated_text, group_id)
    remember.message = f"*[LEMBRETE]* {remember.message}"

    scheduler.add_job(
        action_remember,
        'date',
        run_date=remember.remember_at,
        args=[remember, remote_id],
        id=str(remember.id)
    )
    await send_message(remote_id, feedback_message, message_id)


async def handle_generic_conversation(
        remote_id: str,
        message_id: str,
        user_name: str,
        treated_text: str,
        conversation: str,
        group_id: Optional[int] = None
):
    response_message = await generic_conversation(group_id, user_name, treated_text)

    if "!audio" in conversation.lower():
        audio_base64 = await text_to_speech(
            response_message.get("text"),
            language=response_message.get("language")
        )
        await send_audio(remote_id, audio_base64, message_id)
    else:
        response_text = f"{response_message.get('text')}"
        await send_message(remote_id, response_text, message_id)


def has_explicit_command(text: str) -> bool:
    return any(cmd in text.lower() for cmd, _ in COMMANDS if cmd.startswith("!"))
