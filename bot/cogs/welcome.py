"""Welcome messages and onboarding for the community Discord bot."""
from __future__ import annotations

import logging
from typing import Optional

import discord
from discord.ext import commands

from ..config import BotConfig

log = logging.getLogger(__name__)


class WelcomeCog(commands.Cog):
    """Send welcome messages and log member events."""

    def __init__(self, bot: commands.Bot, config: BotConfig) -> None:
        self.bot = bot
        self.config = config

    async def _get_channel(self, channel_id: Optional[int]) -> Optional[discord.TextChannel]:
        if channel_id is None:
            return None
        channel = self.bot.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        log.info("Member joined: %s", member)
        welcome_channel = await self._get_channel(self.config.discord.welcome_channel_id)
        if welcome_channel:
            await welcome_channel.send(
                f"👋 Hi, {member.mention}! Welcome to {member.guild.name}!"
                " Check out the rules and introduce yourself in chat!"
            )

        if self.config.discord.autorole_ids:
            roles = [member.guild.get_role(role_id) for role_id in self.config.discord.autorole_ids]
            roles_to_add = [role for role in roles if role is not None]
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Auto role assignment")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        log.info("Member left: %s", member)
        log_channel = await self._get_channel(self.config.discord.log_channel_id)
        if log_channel:
            await log_channel.send(f"👋 {member} has left the server.")
