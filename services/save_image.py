import base64
import io
from datetime import datetime
from typing import Optional
from uuid import uuid4

from PIL import Image
from transformers import AutoProcessor, AutoModel
import torch

from database import PgConnection
from database.models.base import Group, User
from database.models.content import Media, Message
from database.operations.base import GroupRepository, UserRepository
from database.operations.content import MediaRepository, MessageRepository
from s3 import S3Client
from services import translate_to_pt


import base64
import io

from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration


def generate_title_image(base64_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(base64.b64decode(base64_bytes)))

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    inputs = processor(image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=20)

    caption = processor.decode(output[0], skip_special_tokens=True)
    return caption

model_name = "google/siglip-base-patch16-224"

processor = AutoProcessor.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval()

async def materialize_image(message_id: str, image_base64: bytes, group_id: Optional[int] = None, user_id: Optional[int] = None) -> Media:
    s3_conn = S3Client()
    _ = await s3_conn.connect()
    async with PgConnection() as db:
        if group_id is not None:
            group_repo = GroupRepository(Group, db)
            group = await group_repo.find_by_id(group_id)
            ext_id = group.ext_id
        else:
            user_repo = UserRepository(User, db)
            user = await user_repo.find_by_id(user_id)
            ext_id = user.ext_id

        decoded = base64.b64decode(image_base64)

        image = Image.open(io.BytesIO(decoded)).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")

        name = generate_title_image(image_base64)
        translated_name = translate_to_pt(name)

        inputs_text = processor(
            text=[translated_name],
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to("cpu")

        with torch.no_grad():
            emb = model.get_image_features(**inputs)
            text_emb = model.get_text_features(**inputs_text)

        emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
        emb = emb.squeeze(0).cpu().numpy()

        text_emb = text_emb / text_emb.norm(p=2, dim=-1, keepdim=True)
        text_emb = text_emb.squeeze().cpu().numpy()

        image_id = uuid4()
        path = f"{ext_id}/{datetime.now().strftime("%Y-%m-%d")}/{image_id}.png"
        _ = await s3_conn.upload_image(
            decoded,
            object_name = path
        )

        media_repo = MediaRepository(Media, db)
        message_repo = MessageRepository(Message, db)
        message = await message_repo.find_by_message_id(message_id)
        new_media = await media_repo.insert(
            Media(
                ext_id=image_id, name=translated_name, message_id=message.id,
                bucket="whatsapp", path=path, format="png",
                size=len(decoded) / float((1024 * 1024)), image_embedding=emb.tolist(),
                name_embedding=text_emb.tolist()
            )
        )

        return new_media