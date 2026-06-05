from pathlib import Path

import aiosqlite

from utils import get_base_dir

GiftRow = tuple[int, int | None, int | None]


class Database:
    def __init__(self, db_file_path: Path = get_base_dir() / "db.db"):
        self.db_file_path = db_file_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.db_file_path)
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gifts (
                gift_id INTEGER PRIMARY KEY,
                upgrade_price INTEGER DEFAULT NULL,
                custom_emoji_id INTEGER DEFAULT NULL
            )
            """
        )
        await self.conn.commit()

    async def get_gifts(self) -> set[GiftRow]:
        async with self.conn.execute(
            "SELECT gift_id, upgrade_price, custom_emoji_id FROM gifts"
        ) as cursor:
            rows = await cursor.fetchall()
        return {(gift_id, upgrade_price, custom_emoji_id) for gift_id, upgrade_price, custom_emoji_id in rows}

    async def add_gift(
        self,
        gift_id: int,
        upgrade_price: int | None,
        custom_emoji_id: int | None = None,
    ) -> None:
        await self.conn.execute(
            "INSERT OR REPLACE INTO gifts (gift_id, upgrade_price, custom_emoji_id) VALUES (?, ?, ?)",
            (gift_id, upgrade_price, custom_emoji_id),
        )
        await self.conn.commit()

    async def update_upgrade_price(self, gift_id: int, upgrade_price: int | None) -> None:
        await self.conn.execute(
            "UPDATE gifts SET upgrade_price = ? WHERE gift_id = ?",
            (upgrade_price, gift_id),
        )
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None
