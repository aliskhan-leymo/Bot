"""Moderation commands for the community Discord bot."""
from __future__ import annotations

import logging
from typing import Optional

import discord
from discord.ext import commands

from ..config import BotConfig

log = logging.getLogger(__name__)


class ModerationCog(commands.Cog):
    """Moderation commands such as kick, ban and purge."""

    def __init__(self, bot: commands.Bot, config: BotConfig) -> None:
        self.bot = bot
        self.config = config

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage("Moderation commands cannot be used in DMs.")
        return True

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        """Kick a member from the guild."""
        await member.kick(reason=reason)
        await ctx.send(
            f"👢 {member.mention} has been kicked. Reason: {reason or 'not provided.'}"
        )
        log.info("%s kicked %s (reason: %s)", ctx.author, member, reason)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None) -> None:
        """Ban a member from the guild."""
        await member.ban(reason=reason)
        await ctx.send(
            f"🔨 {member.mention} has been banned. Reason: {reason or 'not provided.'}"
        )
        log.info("%s banned %s (reason: %s)", ctx.author, member, reason)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, username: str) -> None:
        """Unban a user by username#discriminator."""
        banned_entries = await ctx.guild.bans()  # type: ignore[union-attr]
        name, _, discriminator = username.partition("#")

        for ban_entry in banned_entries:
            user = ban_entry.user
            if user.name == name and user.discriminator == discriminator:
                await ctx.guild.unban(user)  # type: ignore[union-attr]
                await ctx.send(f"✅ {username} has been unbanned.")
                log.info("%s unbanned %s", ctx.author, username)
                return

        await ctx.send("User not found in the ban list.")

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, limit: int = 10) -> None:
        """Delete the last `limit` messages in the channel."""
        deleted = await ctx.channel.purge(limit=limit + 1)
        await ctx.send(
            f"🧹 Deleted messages: {len(deleted) - 1}",
            delete_after=5,
        )
        log.info("%s purged %s messages", ctx.author, limit)

    @kick.error
    @ban.error
    @unban.error
    @purge.error
    async def moderation_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Check the command format.")
        else:
            log.exception("Moderation command error: %s", error)
            await ctx.send("An error occurred while executing the command.")
