"""Integrations with external services such as Google Sheets, Trello and GitHub."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aiohttp
from discord.ext import commands

try:
    import gspread
except ImportError:  # pragma: no cover - optional dependency
    gspread = None

from ..config import BotConfig

log = logging.getLogger(__name__)


class IntegrationsCog(commands.Cog):
    """Commands that bridge the community with productivity tools."""

    def __init__(self, bot: commands.Bot, config: BotConfig) -> None:
        self.bot = bot
        self.config = config
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self) -> None:
        self._http_session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        if self._http_session:
            await self._http_session.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._http_session:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    # Google Sheets -----------------------------------------------------
    async def _append_to_sheet(self, row: list[str]) -> str:
        if not self.config.integrations.google_service_account_file or not self.config.integrations.google_sheet_id:
            raise RuntimeError("Google Sheets integration is not configured.")
        if gspread is None:
            raise RuntimeError("gspread is not installed. Add it to the environment to use this feature.")

        def _sync_append() -> None:
            gc = gspread.service_account(filename=self.config.integrations.google_service_account_file)
            sheet = gc.open_by_key(self.config.integrations.google_sheet_id)
            worksheet = sheet.sheet1
            worksheet.append_row(row, value_input_option="USER_ENTERED")

        await asyncio.to_thread(_sync_append)
        return "Row appended to Google Sheet successfully."

    @commands.command(name="sheet")
    async def sheet(self, ctx: commands.Context, *, comma_separated_values: str) -> None:
        """Append a comma separated row to the configured Google Sheet."""
        values = [value.strip() for value in comma_separated_values.split(",")]
        try:
            result = await self._append_to_sheet(values)
        except Exception as exc:  # pragma: no cover - network interaction
            log.exception("Failed to append to Google Sheet: %s", exc)
            await ctx.send(f"Failed to append data to Google Sheets: {exc}")
            return
        await ctx.send(result)

    # Trello ------------------------------------------------------------
    async def _create_trello_card(self, name: str, description: str) -> str:
        if not (self.config.integrations.trello_key and self.config.integrations.trello_token and self.config.integrations.trello_list_id):
            raise RuntimeError("Trello integration is not configured.")
        session = await self._get_session()
        url = "https://api.trello.com/1/cards"
        payload = {
            "key": self.config.integrations.trello_key,
            "token": self.config.integrations.trello_token,
            "idList": self.config.integrations.trello_list_id,
            "name": name,
            "desc": description,
        }
        async with session.post(url, data=payload, timeout=30) as response:
            if response.status != 200:
                text = await response.text()
                raise RuntimeError(f"Trello API error: {response.status} — {text}")
            data = await response.json()
        return f"Created Trello card: {data.get('shortUrl', 'no link')}"

    @commands.command(name="trello")
    async def trello(self, ctx: commands.Context, *, args: str) -> None:
        """Create a Trello card. Usage: !trello Title | Description"""
        name, sep, description = args.partition("|")
        if not sep:
            await ctx.send("Use the format: !trello Title | Description")
            return
        try:
            result = await self._create_trello_card(name.strip(), description.strip())
        except Exception as exc:  # pragma: no cover - network interaction
            log.exception("Failed to create Trello card: %s", exc)
            await ctx.send(f"Failed to create Trello card: {exc}")
            return
        await ctx.send(result)

    # GitHub ------------------------------------------------------------
    async def _create_github_issue(self, repo: str, title: str, body: str) -> str:
        if not self.config.integrations.github_token:
            raise RuntimeError("GitHub integration is not configured.")
        session = await self._get_session()
        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {
            "Authorization": f"token {self.config.integrations.github_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "CommunityBot/1.0",
        }
        payload = {"title": title, "body": body}
        async with session.post(url, json=payload, headers=headers, timeout=30) as response:
            if response.status >= 300:
                text = await response.text()
                raise RuntimeError(f"GitHub API error: {response.status} — {text}")
            data = await response.json()
        return f"Created issue: {data.get('html_url', 'no link')}"

    @commands.command(name="github")
    async def github(self, ctx: commands.Context, *, args: str) -> None:
        """Create a GitHub issue. Usage: !github [owner/repo] | Title | Description"""
        parts = [part.strip() for part in args.split("|")]
        if len(parts) == 2:
            repo = self.config.integrations.github_default_repo
            title, body = parts
        elif len(parts) == 3:
            repo, title, body = parts
        else:
            await ctx.send("Use the format: !github [repo] | Title | Description")
            return

        if not repo:
            await ctx.send("No GitHub repository provided and no default repository configured.")
            return

        try:
            result = await self._create_github_issue(repo, title, body)
        except Exception as exc:  # pragma: no cover - network interaction
            log.exception("Failed to create GitHub issue: %s", exc)
            await ctx.send(f"Failed to create GitHub issue: {exc}")
            return
        await ctx.send(result)

    # Error handling ----------------------------------------------------
    @sheet.error
    @trello.error
    @github.error
    async def integration_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing arguments for the command.")
        else:
            log.exception("Integration command error: %s", error)
            await ctx.send("An error occurred while running the integration command.")
