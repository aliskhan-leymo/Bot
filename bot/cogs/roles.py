"""Automatic role assignment utilities."""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ..config import BotConfig

log = logging.getLogger(__name__)


class AutoRoleCog(commands.Cog):
    """Commands to manage automatic role assignment."""

    def __init__(self, bot: commands.Bot, config: BotConfig) -> None:
        self.bot = bot
        self.config = config

    @commands.group(name="autorole", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx: commands.Context) -> None:
        """Show configured auto roles."""
        if not self.config.discord.autorole_ids:
            await ctx.send("Automatic roles are not configured.")
            return

        roles = [ctx.guild.get_role(role_id) for role_id in self.config.discord.autorole_ids]  # type: ignore[union-attr]
        roles_list = ", ".join(role.mention for role in roles if role is not None)
        await ctx.send(f"Roles assigned automatically: {roles_list}")

    @autorole.command(name="give")
    @commands.has_permissions(manage_roles=True)
    async def autorole_give(self, ctx: commands.Context, member: discord.Member) -> None:
        """Manually trigger the auto role assignment for a user."""
        if not self.config.discord.autorole_ids:
            await ctx.send("Automatic roles are not configured.")
            return

        roles = [ctx.guild.get_role(role_id) for role_id in self.config.discord.autorole_ids]  # type: ignore[union-attr]
        roles_to_add = [role for role in roles if role is not None]
        if not roles_to_add:
            await ctx.send("No configured roles could be found.")
            return

        await member.add_roles(*roles_to_add, reason="Manual auto-role assignment")
        await ctx.send(f"Roles assigned to {member.display_name}.")

    @autorole.error
    @autorole_give.error
    async def autorole_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to modify auto roles.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Unable to find the specified user or channel.")
        else:
            log.exception("Auto role command error: %s", error)
            await ctx.send("An error occurred while executing the command.")
