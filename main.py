import asyncio
import logging

from pyrogram import Client, enums

from config import (
    API_HASH,
    API_ID,
    CHANNEL_ID,
    CHECK_INTERVAL,
    PHONE,
    SESSION_NAME,
    STATUS_CHAT_ID,
    STATUS_INTERVAL,
    STICKERSET_SHORT_NAME,
    STICKERSET_TITLE,
)
from database import Database
from emoji_creator import EmojiCreator
from gift_checker import StarGiftUpgradeChecker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def run() -> None:
    while True:
        db = Database()
        try:
            await db.connect()
            async with Client(
                name=SESSION_NAME,
                api_id=API_ID,
                api_hash=API_HASH,
                phone_number=PHONE,
                no_updates=True,
                parse_mode=enums.ParseMode.HTML,
            ) as client:
                emoji_creator = EmojiCreator(
                    client=client,
                    stickerset_title=STICKERSET_TITLE,
                    stickerset_short_name=STICKERSET_SHORT_NAME,
                )
                checker = StarGiftUpgradeChecker(
                    client=client,
                    db=db,
                    emoji_creator=emoji_creator,
                    channel_id=CHANNEL_ID,
                    status_chat_id=STATUS_CHAT_ID,
                    check_interval=CHECK_INTERVAL,
                    status_interval=STATUS_INTERVAL,
                )
                await checker.run()
        except Exception as exc:
            logger.error(f"Session crashed, restarting | session={SESSION_NAME} | {exc}")
        finally:
            await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
