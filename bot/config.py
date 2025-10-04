"""Configuration helpers for the Discord bot."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiscordConfig:
    token: str
    guild_id: Optional[int]
    command_prefix: str
    welcome_channel_id: Optional[int]
    log_channel_id: Optional[int]
    autorole_ids: tuple[int, ...]


@dataclass(frozen=True)
class ReminderConfig:
    storage_path: str
    check_interval: int


@dataclass(frozen=True)
class IntegrationConfig:
    google_service_account_file: Optional[str]
    google_sheet_id: Optional[str]
    trello_key: Optional[str]
    trello_token: Optional[str]
    trello_list_id: Optional[str]
    github_token: Optional[str]
    github_default_repo: Optional[str]


@dataclass(frozen=True)
class BotConfig:
    discord: DiscordConfig
    reminders: ReminderConfig
    integrations: IntegrationConfig


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def _parse_int_list(value: Optional[str]) -> tuple[int, ...]:
    if not value:
        return ()
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def load_config() -> BotConfig:
    """Load the bot configuration from environment variables."""

    discord_config = DiscordConfig(
        token=os.environ.get("DISCORD_TOKEN", ""),
        guild_id=_parse_int(os.environ.get("DISCORD_GUILD_ID")),
        command_prefix=os.environ.get("DISCORD_COMMAND_PREFIX", "!"),
        welcome_channel_id=_parse_int(os.environ.get("DISCORD_WELCOME_CHANNEL_ID")),
        log_channel_id=_parse_int(os.environ.get("DISCORD_LOG_CHANNEL_ID")),
        autorole_ids=_parse_int_list(os.environ.get("DISCORD_AUTOROLE_IDS")),
    )

    reminders = ReminderConfig(
        storage_path=os.environ.get("REMINDER_STORAGE", "data/reminders.json"),
        check_interval=int(os.environ.get("REMINDER_CHECK_INTERVAL", "60")),
    )

    integrations = IntegrationConfig(
        google_service_account_file=os.environ.get("GOOGLE_SERVICE_ACCOUNT"),
        google_sheet_id=os.environ.get("GOOGLE_SHEET_ID"),
        trello_key=os.environ.get("TRELLO_KEY"),
        trello_token=os.environ.get("TRELLO_TOKEN"),
        trello_list_id=os.environ.get("TRELLO_LIST_ID"),
        github_token=os.environ.get("GITHUB_TOKEN"),
        github_default_repo=os.environ.get("GITHUB_DEFAULT_REPO"),
    )

    if not discord_config.token:
        raise RuntimeError("DISCORD_TOKEN environment variable must be set.")

    return BotConfig(
        discord=discord_config,
        reminders=reminders,
        integrations=integrations,
    )
