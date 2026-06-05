import logging

from pyrogram import Client
from pyrogram.file_id import FileId
from pyrogram.raw.functions.messages import GetMyStickers
from pyrogram.raw.functions.stickers import AddStickerToSet, CreateStickerSet
from pyrogram.raw.types import (
    InputDocument,
    InputStickerSetItem,
    InputStickerSetShortName,
    InputUserSelf,
)
from pyrogram.raw.types.messages import StickerSet
from pyrogram.types import Gift

logger = logging.getLogger(__name__)


class EmojiCreator:
    def __init__(self, client: Client, stickerset_title: str, stickerset_short_name: str):
        self.client = client
        self.stickerset_title = stickerset_title
        self.stickerset_short_name = stickerset_short_name
        self.stickerset: StickerSet | None = None
        self.existing_document_ids: set[int] = set()

    async def initialize_stickerset(self) -> bool:
        my_stickersets = await self.client.invoke(GetMyStickers(offset_id=0, limit=1000000))
        for stickerset in my_stickersets.sets:
            if stickerset.set.short_name == self.stickerset_short_name:
                self.stickerset = stickerset
                self.existing_document_ids = {doc.id for doc in stickerset.documents}
                logger.info(f"Stickerset already exists | {self.stickerset_short_name}")
                return True

        logger.info(f"Stickerset not found, will be created on first gift | {self.stickerset_short_name}")
        return False

    async def add_gift_to_stickerset(self, gift: Gift) -> int | None:
        try:
            file_id = FileId.decode(gift.sticker.file_id)
            document = InputDocument(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
            )
            sticker = InputStickerSetItem(
                document=document,
                emoji=gift.sticker.emoji or "🎁",
            )

            if not self.stickerset:
                self.stickerset = await self.client.invoke(CreateStickerSet(
                    user_id=InputUserSelf(),
                    title=self.stickerset_title,
                    short_name=self.stickerset_short_name,
                    stickers=[sticker],
                    emojis=True,
                ))
                logger.info(f"Stickerset created | {self.stickerset_short_name}")
            else:
                self.stickerset = await self.client.invoke(AddStickerToSet(
                    stickerset=InputStickerSetShortName(short_name=self.stickerset_short_name),
                    sticker=sticker,
                ))

            new_document_id: int | None = None
            for doc in self.stickerset.documents:
                if doc.id not in self.existing_document_ids:
                    new_document_id = doc.id
                    break

            if new_document_id is None:
                logger.warning(f"Failed to extract custom_emoji_id | gift_id={gift.id}")
                return None

            self.existing_document_ids.add(new_document_id)
            logger.info(f"Custom emoji created | gift_id={gift.id} emoji_id={new_document_id}")
            return new_document_id

        except Exception as exc:
            logger.error(f"Failed to add gift sticker | gift_id={gift.id} | {exc}")
            return None
