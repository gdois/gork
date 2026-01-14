import base64
import subprocess
import tempfile
import os
import math

import numpy as np
import httpx
from PIL import Image, ImageFont

from external.evolution import download_media
from functions.sticker import add_caption_to_image


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


def calculate_font_size(text: str, max_height: int) -> int:
    base_size = max(20, int(max_height * 0.08))

    text_length = len(text)
    if text_length > 100:
        return max(20, int(base_size * 0.6))
    elif text_length > 50:
        return max(25, int(base_size * 0.75))
    elif text_length > 30:
        return max(30, int(base_size * 0.85))
    else:
        return base_size


def split_text_smart(text: str, max_chars_per_line: int = 25) -> tuple[str, str]:
    if "|" in text:
        parts = text.split("|", 1)
        return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""

    words = text.split()

    if len(text) <= max_chars_per_line:
        return text, ""

    mid_point = len(words) // 2

    top_text = " ".join(words[:mid_point])
    bottom_text = " ".join(words[mid_point:])

    if len(top_text) > max_chars_per_line * 2:
        top_words = []
        current_length = 0
        for word in words:
            if current_length + len(word) + 1 > max_chars_per_line * 2:
                break
            top_words.append(word)
            current_length += len(word) + 1

        top_text = " ".join(top_words)
        bottom_text = " ".join(words[len(top_words):])

    return top_text, bottom_text


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [text]


def add_caption_to_gif_frames(gif_path: str, caption_text: str, output_path: str) -> str:
    gif = Image.open(gif_path)
    frames = []
    durations = []

    try:
        frame_index = 0
        while True:
            frame = gif.copy()
            if frame.mode != 'RGB':
                if frame.mode == 'P':
                    frame = frame.convert('RGBA').convert('RGB')
                else:
                    frame = frame.convert('RGB')

            frame_with_caption = add_caption_to_image(frame, caption_text)
            frames.append(frame_with_caption)

            durations.append(gif.info.get('duration', 66))

            frame_index += 1
            gif.seek(frame_index)
    except EOFError:
        pass

    frames[0].save(
        output_path,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False
    )

    return output_path


def apply_bulge_effect(frame: Image.Image, intensity: float = 0.5) -> Image.Image:
    img_array = np.array(frame)
    height, width = img_array.shape[:2]

    center_x, center_y = width // 2, height // 2

    max_radius = math.sqrt(center_x ** 2 + center_y ** 2)

    new_img = np.zeros_like(img_array)

    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < max_radius:
                factor = 1.0 - (distance / max_radius)
                factor = math.pow(factor, 2) * intensity

                new_distance = distance * (1 + factor)

                if new_distance < max_radius:
                    angle = math.atan2(dy, dx)
                    src_x = int(center_x + new_distance * math.cos(angle))
                    src_y = int(center_y + new_distance * math.sin(angle))

                    if 0 <= src_x < width and 0 <= src_y < height:
                        new_img[y, x] = img_array[src_y, src_x]
                    else:
                        new_img[y, x] = img_array[y, x]
                else:
                    new_img[y, x] = img_array[y, x]
            else:
                new_img[y, x] = img_array[y, x]

    return Image.fromarray(new_img)


def apply_pinch_effect(frame: Image.Image, intensity: float = 0.5) -> Image.Image:
    img_array = np.array(frame)
    height, width = img_array.shape[:2]

    center_x, center_y = width // 2, height // 2
    max_radius = math.sqrt(center_x ** 2 + center_y ** 2)

    new_img = np.zeros_like(img_array)

    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < max_radius:
                factor = 1.0 - (distance / max_radius)
                factor = math.pow(factor, 2) * intensity

                new_distance = distance * (1 - factor * 0.5)

                angle = math.atan2(dy, dx)
                src_x = int(center_x + new_distance * math.cos(angle))
                src_y = int(center_y + new_distance * math.sin(angle))

                if 0 <= src_x < width and 0 <= src_y < height:
                    new_img[y, x] = img_array[src_y, src_x]
                else:
                    new_img[y, x] = img_array[y, x]
            else:
                new_img[y, x] = img_array[y, x]

    return Image.fromarray(new_img)


def apply_swirl_effect(frame: Image.Image, intensity: float = 0.5) -> Image.Image:
    img_array = np.array(frame)
    height, width = img_array.shape[:2]

    center_x, center_y = width // 2, height // 2
    max_radius = math.sqrt(center_x ** 2 + center_y ** 2)

    new_img = np.zeros_like(img_array)

    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < max_radius:
                factor = 1.0 - (distance / max_radius)
                rotation = factor * intensity * math.pi * 2

                angle = math.atan2(dy, dx) + rotation

                src_x = int(center_x + distance * math.cos(angle))
                src_y = int(center_y + distance * math.sin(angle))

                if 0 <= src_x < width and 0 <= src_y < height:
                    new_img[y, x] = img_array[src_y, src_x]
                else:
                    new_img[y, x] = img_array[y, x]
            else:
                new_img[y, x] = img_array[y, x]

    return Image.fromarray(new_img)


def apply_wave_effect(frame: Image.Image, intensity: float = 10) -> Image.Image:
    img_array = np.array(frame)
    height, width = img_array.shape[:2]

    new_img = np.zeros_like(img_array)

    for y in range(height):
        offset = int(intensity * math.sin(y * 0.1))
        for x in range(width):
            src_x = (x + offset) % width
            new_img[y, x] = img_array[y, src_x]

    return Image.fromarray(new_img)


def apply_fisheye_effect(frame: Image.Image, intensity: float = 0.5) -> Image.Image:
    img_array = np.array(frame)
    height, width = img_array.shape[:2]

    center_x, center_y = width // 2, height // 2
    max_radius = min(center_x, center_y)

    new_img = np.copy(img_array)

    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < max_radius:
                norm_distance = distance / max_radius

                new_distance = max_radius * math.pow(norm_distance, 1 + intensity)

                angle = math.atan2(dy, dx)
                src_x = int(center_x + new_distance * math.cos(angle))
                src_y = int(center_y + new_distance * math.sin(angle))

                if 0 <= src_x < width and 0 <= src_y < height:
                    new_img[y, x] = img_array[src_y, src_x]

    return Image.fromarray(new_img)


def apply_explosion_effect(frame: Image.Image, progress: float) -> Image.Image:
    intensity = progress * 1.5

    frame = apply_bulge_effect(frame, intensity)

    if progress > 0.5:
        swirl_intensity = (progress - 0.5) * 2 * 0.3
        frame = apply_swirl_effect(frame, swirl_intensity)

    return frame


def apply_breathing_effect(frame: Image.Image, progress: float) -> Image.Image:
    intensity = math.sin(progress * math.pi * 2) * 0.3

    if intensity > 0:
        return apply_bulge_effect(frame, intensity)
    else:
        return apply_pinch_effect(frame, abs(intensity))


def add_effect_to_gif_frames(gif_path: str, output_path: str, effect: str = "bulge") -> str:
    """
    Aplica efeitos de distorção a um GIF.

    Efeitos disponíveis:
    - "bulge": Efeito de balão/infla
    - "pinch": Efeito de pinça/implode
    - "swirl": Efeito de redemoinho
    - "wave": Efeito de ondas
    - "fisheye": Efeito olho de peixe
    - "explosion": Efeito de explosão animado
    - "breathing": Efeito de respiração animado
    """
    gif = Image.open(gif_path)
    frames = []
    durations = []

    frame_count = 0
    try:
        while True:
            frame = gif.copy()
            if frame.mode != 'RGB':
                if frame.mode == 'P':
                    frame = frame.convert('RGBA').convert('RGB')
                else:
                    frame = frame.convert('RGB')

            try:
                total_frames = gif.n_frames
            except:
                total_frames = 30

            progress = frame_count / max(total_frames - 1, 1)

            if effect == "bulge":
                frame_effect = apply_bulge_effect(frame, 0.5)
            elif effect == "pinch":
                frame_effect = apply_pinch_effect(frame, 0.5)
            elif effect == "swirl":
                frame_effect = apply_swirl_effect(frame, 0.5)
            elif effect == "wave":
                frame_effect = apply_wave_effect(frame, 10)
            elif effect == "fisheye":
                frame_effect = apply_fisheye_effect(frame, 0.5)
            elif effect == "explosion":
                frame_effect = apply_explosion_effect(frame, progress)
            elif effect == "breathing":
                frame_effect = apply_breathing_effect(frame, progress)
            else:
                frame_effect = frame

            frames.append(frame_effect)
            durations.append(gif.info.get('duration', 66))

            frame_count += 1
            gif.seek(frame_count)
    except EOFError:
        pass

    frames[0].save(
        output_path,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False
    )

    return output_path


async def animated(message_id: str, caption_text: str = None, effect: str = None) -> str:
    video_base64 = await download_media(message_id, True)
    video_data = base64.b64decode(video_base64[0])

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_temp:
        video_temp.write(video_data)
        video_path = video_temp.name

    gif_path = tempfile.mktemp(suffix='.gif')
    gif_with_caption_path = tempfile.mktemp(suffix='.gif')
    gif_with_effect_path = tempfile.mktemp(suffix='.gif')

    try:
        subprocess.run([
            'ffmpeg',
            '-i', video_path,
            '-vf',
            'fps=15,'
            'scale=512:512:force_original_aspect_ratio=increase:flags=lanczos,'
            'crop=512:512,'
            'split[s0][s1];'
            '[s0]palettegen=max_colors=256[p];'
            '[s1][p]paletteuse=dither=bayer:bayer_scale=5',
            '-t', '5',
            '-loop', '0',
            gif_path,
            '-y'
        ], check=True, capture_output=True)

        final_gif_path = gif_path

        if caption_text:
            final_gif_path = add_caption_to_gif_frames(gif_path, caption_text, gif_with_caption_path)

        if effect:
            input_for_effect = final_gif_path
            final_gif_path = add_effect_to_gif_frames(input_for_effect, gif_with_effect_path, effect)

        gif_url = await upload_to_tmpfile(final_gif_path)

        return gif_url

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise Exception(f"Erro ao processar vídeo: {error_msg}")

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(gif_path):
            os.remove(gif_path)
        if os.path.exists(gif_with_caption_path):
            os.remove(gif_with_caption_path)
        if os.path.exists(gif_with_effect_path):
            os.remove(gif_with_effect_path)