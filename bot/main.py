"""Entry point for the community Discord bot."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from .config import BotConfig, load_config
from .utils.logging import setup_logging
from .cogs.moderation import ModerationCog
from .cogs.welcome import WelcomeCog
from .cogs.roles import AutoRoleCog
from .cogs.reminders import RemindersCog
from .cogs.integrations import IntegrationsCog


async def _setup_bot(config: BotConfig) -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.guilds = True
    intents.reactions = True

    bot = commands.Bot(command_prefix=config.discord.command_prefix, intents=intents)

    await bot.add_cog(ModerationCog(bot, config))
    await bot.add_cog(WelcomeCog(bot, config))
    await bot.add_cog(AutoRoleCog(bot, config))
    await bot.add_cog(RemindersCog(bot, config))
    await bot.add_cog(IntegrationsCog(bot, config))

    return bot


async def main() -> None:
    """Start the Discord bot."""
    setup_logging()
    config = load_config()

    Path("data").mkdir(parents=True, exist_ok=True)

    bot = await _setup_bot(config)

    logging.getLogger(__name__).info("Starting bot with prefix '%s'", config.discord.command_prefix)
    await bot.start(config.discord.token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot shutdown requested by user.")
