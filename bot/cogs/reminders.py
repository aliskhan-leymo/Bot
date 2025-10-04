"""Event reminder scheduler for the community Discord bot."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import discord
from discord.ext import commands, tasks

from ..config import BotConfig

log = logging.getLogger(__name__)


@dataclass
class Reminder:
    id: int
    guild_id: int
    channel_id: int
    message: str
    remind_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(
            id=int(data["id"]),
            guild_id=int(data["guild_id"]),
            channel_id=int(data["channel_id"]),
            message=data["message"],
            remind_at=datetime.fromisoformat(data["remind_at"]),
        )

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["remind_at"] = self.remind_at.isoformat()
        return payload


class RemindersCog(commands.Cog):
    """Schedule and deliver reminder messages."""

    def __init__(self, bot: commands.Bot, config: BotConfig) -> None:
        self.bot = bot
        self.config = config
        self.storage = Path(config.reminders.storage_path)
        self._reminders: List[Reminder] = []
        self._loop_task.start()

    async def cog_load(self) -> None:
        await self._load_reminders()

    def cog_unload(self) -> None:
        self._loop_task.cancel()

    async def _load_reminders(self) -> None:
        if not self.storage.exists():
            return
        try:
            data = json.loads(self.storage.read_text("utf-8"))
        except json.JSONDecodeError as exc:
            log.error("Failed to parse reminder storage: %s", exc)
            return
        self._reminders = [Reminder.from_dict(item) for item in data]
        log.info("Loaded %d reminders", len(self._reminders))

    async def _save_reminders(self) -> None:
        payload = [reminder.to_dict() for reminder in self._reminders]
        tmp_path = self.storage.with_suffix(".tmp")
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
        tmp_path.replace(self.storage)

    def _next_id(self) -> int:
        if not self._reminders:
            return 1
        return max(reminder.id for reminder in self._reminders) + 1

    @commands.group(name="remind", invoke_without_command=True)
    async def remind(self, ctx: commands.Context) -> None:
        """List upcoming reminders."""
        if not self._reminders:
            await ctx.send("There are no reminders yet. Add one with `!remind add`.")
            return

        upcoming = sorted((r for r in self._reminders if r.guild_id == ctx.guild.id), key=lambda r: r.remind_at)  # type: ignore[union-attr]
        if not upcoming:
            await ctx.send("This server has no active reminders.")
            return

        lines = [
            f"#{reminder.id}: {reminder.message} — {reminder.remind_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            for reminder in upcoming
        ]
        await ctx.send("\n".join(lines))

    @remind.command(name="add")
    async def remind_add(self, ctx: commands.Context, datetime_str: str, *, message: str) -> None:
        """Add a reminder. Time format: YYYY-MM-DDTHH:MM (24h)."""
        try:
            remind_at = datetime.fromisoformat(datetime_str)
            if remind_at.tzinfo is None:
                remind_at = remind_at.replace(tzinfo=timezone.utc)
        except ValueError:
            await ctx.send("Invalid date format. Use YYYY-MM-DDTHH:MM")
            return

        reminder = Reminder(
            id=self._next_id(),
            guild_id=ctx.guild.id,  # type: ignore[union-attr]
            channel_id=ctx.channel.id,
            message=message,
            remind_at=remind_at.astimezone(timezone.utc),
        )
        self._reminders.append(reminder)
        await self._save_reminders()
        await ctx.send(
            f"🔔 Reminder #{reminder.id} scheduled for {reminder.remind_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )

    @remind.command(name="remove")
    async def remind_remove(self, ctx: commands.Context, reminder_id: int) -> None:
        """Remove a reminder by its identifier."""
        before_count = len(self._reminders)
        self._reminders = [r for r in self._reminders if not (r.id == reminder_id and r.guild_id == ctx.guild.id)]  # type: ignore[union-attr]
        if len(self._reminders) == before_count:
            await ctx.send("No reminder with that ID was found.")
            return
        await self._save_reminders()
        await ctx.send(f"Reminder #{reminder_id} deleted.")

    @tasks.loop(seconds=60)
    async def _loop_task(self) -> None:
        now = datetime.now(timezone.utc)
        due = [r for r in self._reminders if r.remind_at <= now]
        if not due:
            return

        for reminder in due:
            channel = self.bot.get_channel(reminder.channel_id)
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(f"⏰ Reminder: {reminder.message}")
                except discord.HTTPException as exc:
                    log.error("Failed to send reminder %s: %s", reminder.id, exc)
            else:
                log.warning("Channel %s for reminder %s not found", reminder.channel_id, reminder.id)

        self._reminders = [r for r in self._reminders if r.remind_at > now]
        await self._save_reminders()

    @_loop_task.before_loop
    async def before_loop(self) -> None:
        await self.bot.wait_until_ready()
        await self._load_reminders()

    @_loop_task.error
    async def loop_error(self, error: Exception) -> None:
        log.exception("Reminder loop failed: %s", error)

    @remind.error
    @remind_add.error
    @remind_remove.error
    async def remind_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing arguments. Check the command format.")
        else:
            log.exception("Reminder command error: %s", error)
            await ctx.send("An error occurred while executing the command.")
