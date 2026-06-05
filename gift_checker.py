import asyncio
import logging
import time

from pyrogram import Client, enums
from pyrogram.types import Gift

from database import Database, GiftRow
from emoji_creator import EmojiCreator

logger = logging.getLogger(__name__)

GiftChange = tuple[Gift, int | None, int | None, int | None]


class StarGiftUpgradeChecker:
    def __init__(
        self,
        client: Client,
        db: Database,
        emoji_creator: EmojiCreator,
        channel_id: str,
        status_chat_id: int | str,
        check_interval: int,
        status_interval: int,
    ):
        self.client = client
        self.db = db
        self.emoji_creator = emoji_creator
        self.channel_id = channel_id
        self.status_chat_id = status_chat_id
        self.check_interval = check_interval
        self.status_interval = status_interval

        self.gifts: set[GiftRow] = set()
        self.try_numbers = 0
        self.failed_requests = 0
        self.started_at = time.monotonic()

    async def run(self) -> None:
        self.gifts = await self.db.get_gifts()
        await self.emoji_creator.initialize_stickerset()
        await asyncio.gather(self._monitor_upgrades(), self._report_status())

    async def _monitor_upgrades(self) -> None:
        while True:
            try:
                self.try_numbers += 1
                available_gifts = await self.client.get_available_gifts()
                changes: list[GiftChange] = []

                for gift in available_gifts:
                    new_price = gift.upgrade_price or None
                    old_gift = next((g for g in self.gifts if g[0] == gift.id), None)
                    if old_gift is None:
                        custom_emoji_id = await self.emoji_creator.add_gift_to_stickerset(gift)
                        await self.db.add_gift(gift.id, new_price, custom_emoji_id)
                        changes.append((gift, None, new_price, custom_emoji_id))
                    else:
                        _, old_price, custom_emoji_id = old_gift
                        if old_price != new_price:
                            await self.db.update_upgrade_price(gift.id, new_price)
                            changes.append((gift, old_price, new_price, custom_emoji_id))

                self.gifts = {
                    (
                        gift.id,
                        gift.upgrade_price or None,
                        next((g[2] for g in self.gifts if g[0] == gift.id), None),
                    )
                    for gift in available_gifts
                }

                if changes:
                    await self._post_changes(changes)
            except Exception as exc:
                self.failed_requests += 1
                logger.error(f"Monitoring iteration failed: {exc}")

            await asyncio.sleep(self.check_interval)

    async def _post_changes(self, changes: list[GiftChange]) -> None:
        lines = ["Changes"]
        for gift, old_price, new_price, custom_emoji_id in changes:
            emoji = f"<emoji id={custom_emoji_id}>{gift.sticker.emoji}</emoji>"
            if old_price is not None and new_price is not None:
                lines.append(f"{emoji} {gift.price} ★\n  upgrade price: {old_price} ★ → {new_price} ★")
            elif new_price is not None:
                lines.append(f"{emoji} {gift.price} ★\n  upgrade price: {new_price} ★")
            else:
                lines.append(f"{emoji} {gift.price} ★")

        try:
            await self.client.send_message(chat_id=self.channel_id, text="\n".join(lines))
        except Exception as exc:
            self.failed_requests += 1
            logger.error(f"Failed to post changes | channel={self.channel_id} | {exc}")

    async def _report_status(self) -> None:
        while True:
            await asyncio.sleep(self.status_interval)
            try:
                total = self.try_numbers
                success = total - self.failed_requests
                rate = (success / total * 100) if total else 0.0
                uptime_hours = (time.monotonic() - self.started_at) / 3600
                message = (
                    f"Checker active for {uptime_hours:.1f} h\n"
                    f"Successful requests: {success}/{total}\n"
                    f"Success rate: {rate:.1f}%"
                )
                self.try_numbers = 0
                self.failed_requests = 0
                logger.info(message)
                await self.client.send_message(
                    self.status_chat_id,
                    "⛏️🎁 " + message,
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception as exc:
                logger.error(f"Status report failed | chat={self.status_chat_id} | {exc}")
