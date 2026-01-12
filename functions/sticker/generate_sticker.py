from io import BytesIO
import re
import base64
import subprocess
import tempfile
import os

import httpx
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from rembg import remove

from database.models.base import User
from database.models.content import Message
from database.operations.base import UserRepository
from database.operations.content import MessageRepository
from external.evolution import download_media
from functions.sticker import add_caption_to_image
from s3 import S3Client
from utils import get_env_var


async def generate_sticker(
        webhook_event: dict, caption_text: str,
        db: AsyncSession, medias: dict,
        random_image: bool = False, remove_background: bool = False
) -> str:
    event_data = webhook_event["data"]
    message_id = event_data["key"]["id"]

    image_base64 = None

    available_medias = list(medias.keys())
    if "text_quote" in available_medias:
        message_text, quoted_message_id = medias["text_quote"]
        message_repo = MessageRepository(Message, db)

        message = await message_repo.find_by_message_id(quoted_message_id)
        caption_text = message_text if message_text else caption_text
    else:
        message = None

    if "image_message" in available_medias and image_base64 is None:
        image_base64, _ = await download_media(message_id)
    if "image_quote" in available_medias and image_base64 is None:
        image_base64, _ = await download_media(medias["image_quote"])
    if image_base64 is None and message:
        user_repo = UserRepository(User, db)
        user = await user_repo.find_by_id(message.user_id)

        if caption_text:
            pattern = r'@(\d+)'
            mentions = re.findall(pattern, caption_text)
            users_mentioned = [await user_repo.find_by_phone_or_id(mention) for mention in mentions]
            users_mentions = zip(users_mentioned, mentions)

            for user_m, mention in users_mentions:
                caption_text = caption_text.replace(f"@{mention}", user_m.name)

        if user.profile_pic_path:
            s3_client = S3Client()
            _ = await s3_client.connect()
            image_base64 = await s3_client.get_image_base64("whatsapp", user.profile_pic_path)

    if random_image or image_base64 is None:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.api-ninjas.com/v1/randomimage", headers={"X-Api-Key": get_env_var("NINJA_KEY")})
            image_base64 = response.content

    image_bytes = base64.b64decode(image_base64)

    img = Image.open(BytesIO(image_bytes))

    if remove_background:
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        output = remove(img_bytes.read())
        img = Image.open(BytesIO(output))

    img.thumbnail((512, 512), Image.Resampling.LANCZOS)

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    if caption_text:
        img = add_caption_to_image(img, caption_text)

    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=95)
    buffer.seek(0)
    webp_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return webp_base64

async def upload_to_tmpfile(gif_path: str) -> str:
    URL = "https://tmpfile.link/api/upload"

    async with httpx.AsyncClient() as client:
        with open(gif_path, "rb") as image:
            response = await client.post(
                URL,
                files={
                    "file": (gif_path, image, "image/gif")
                },
                timeout=30
            )

    response.raise_for_status()
    data = response.json()

    return data.get("downloadLink")


def add_caption_to_gif_frames(gif_path: str, caption_text: str, output_path: str) -> str:
    gif = Image.open(gif_path)
    frames = []

    try:
        while True:
            frame = gif.copy().convert('RGBA')

            frame_with_caption = add_caption_to_image(frame, caption_text)
            frames.append(frame_with_caption)

            gif.seek(gif.tell() + 1)
    except EOFError:
        pass

    frames[0].save(
        output_path,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=gif.info.get('duration', 66),
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False
    )

    return output_path


async def generate_animated_sticker(message_id: str, caption_text: str = None) -> str:
    video_base64 = await download_media(message_id, True)
    video_data = base64.b64decode(video_base64[0])

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_temp:
        video_temp.write(video_data)
        video_path = video_temp.name

    gif_path = tempfile.mktemp(suffix='.gif')
    gif_with_caption_path = tempfile.mktemp(suffix='.gif')

    try:
        subprocess.run([
            'ffmpeg',
            '-i', video_path,
            '-vf',
            'fps=15,'
            'scale=512:512:force_original_aspect_ratio=increase:flags=lanczos,'
            'crop=512:512,'
            'split[s0][s1];'
            '[s0]palettegen=max_colors=256:reserve_transparent=1[p];'
            '[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
            '-t', '3',
            '-loop', '0',
            gif_path,
            '-y'
        ], check=True, capture_output=True)

        final_gif_path = gif_path
        if caption_text:
            final_gif_path = add_caption_to_gif_frames(gif_path, caption_text, gif_with_caption_path)

        gif_url = await upload_to_tmpfile(final_gif_path)

        return gif_url

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ Erro FFmpeg: {error_msg}")
        raise Exception(f"Erro ao processar vídeo: {error_msg}")

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(gif_path):
            os.remove(gif_path)
        if os.path.exists(gif_with_caption_path):
            os.remove(gif_with_caption_path)
