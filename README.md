# Gifts Checker

> [Русская версия](README.ru.md)

Telegram userbot that monitors the Star Gifts catalogue and posts a message to a channel whenever a gift appears or its upgrade price changes. Each tracked gift is mirrored as a custom emoji in a personal stickerset so change reports can show the gift sticker inline.

## Features

- Polls `get_available_gifts` on a configurable interval
- Detects new gifts and upgrade price changes, posts a single digest per iteration
- Auto-builds a custom emoji stickerset from gift stickers; reuses `custom_emoji_id` across restarts
- Persists gift state in SQLite so restarts don't re-announce everything
- Periodic status report with uptime and success rate
- Session auto-restart on crash
- Secrets loaded from `.env`

## Project Structure

```
├── main.py            # entry point, logging, client lifecycle
├── gift_checker.py    # monitoring loop, change detection, status report
├── emoji_creator.py   # stickerset creation and custom emoji extraction
├── database.py        # aiosqlite wrapper for the gifts table
├── config.py          # loads settings from .env
├── .env.example       # template for required environment variables
└── requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your Telegram API credentials and channel IDs.

## Usage

```bash
python main.py
```

On first launch Pyrogram will ask for the login code to create the session file.

## Configuration

| Variable | Description |
|---|---|
| `API_ID`, `API_HASH` | Telegram API credentials from [my.telegram.org](https://my.telegram.org) |
| `PHONE` | Phone number in international format (e.g. `+123456789`) |
| `CHANNEL_ID` | Target chat for change notifications (`@username` or numeric id) |
| `STATUS_CHAT_ID` | Chat for periodic status reports (default `me`) |
| `SESSION_NAME` | Pyrogram session filename (no extension) |
| `DB_FILE_PATH` | Path to SQLite database file |
| `STICKERSET_TITLE` | Display title of the stickerset |
| `STICKERSET_SHORT_NAME` | Unique short name of the stickerset (must be globally unique) |
| `CHECK_INTERVAL` | Seconds between gift snapshots (default `30`) |
| `STATUS_INTERVAL` | Seconds between status reports (default `3600`) |

## How It Works

1. On startup the checker loads previously seen gifts from SQLite and locates its custom emoji stickerset (creating a fresh one on the first new gift if it doesn't exist).
2. Every `CHECK_INTERVAL` seconds the monitor fetches the current gift catalogue. New gifts are added to the stickerset and stored; existing gifts are compared by `upgrade_price`.
3. If any changes are found in an iteration, a single HTML post is sent to `CHANNEL_ID`, with each gift rendered as its custom emoji alongside the price delta.
4. Every `STATUS_INTERVAL` seconds a short success-rate report is sent to `STATUS_CHAT_ID`.
