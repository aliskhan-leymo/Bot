# Community Discord Bot

A multifunctional Discord bot for community management. It combines moderation tools, welcome and auto-role flows, event reminders, and integrations with Google Sheets, Trello, and GitHub.

## Features

- **Moderation**: `!kick`, `!ban`, `!unban`, and `!purge` commands with error handling and logging.
- **Welcome & auto-roles**: welcome announcements, starter role assignment, and leave notifications.
- **Event reminders**: the `!remind` command to create, list, and remove reminders stored in `data/reminders.json`.
- **Integrations**:
  - Google Sheets — append rows to a spreadsheet.
  - Trello — create cards in a configured list.
  - GitHub — open issues in repositories.

## Quick start

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in the values (or export the environment variables another way).

3. Run the bot:

   ```bash
   python -m bot.main
   ```

## Environment variables

| Variable | Description |
| --- | --- |
| `DISCORD_TOKEN` | Discord bot token. **Required.** |
| `DISCORD_GUILD_ID` | Default guild ID (optional). |
| `DISCORD_COMMAND_PREFIX` | Command prefix (defaults to `!`). |
| `DISCORD_WELCOME_CHANNEL_ID` | Channel for welcome messages. |
| `DISCORD_LOG_CHANNEL_ID` | Channel for leave notifications. |
| `DISCORD_AUTOROLE_IDS` | Comma-separated role IDs to assign automatically. |
| `REMINDER_STORAGE` | Path to the reminder storage file (defaults to `data/reminders.json`). |
| `REMINDER_CHECK_INTERVAL` | Reminder polling interval in seconds (defaults to `60`). |
| `GOOGLE_SERVICE_ACCOUNT` | Path to the Google service account JSON file. |
| `GOOGLE_SHEET_ID` | Google Sheets spreadsheet ID. |
| `TRELLO_KEY` | Trello API key. |
| `TRELLO_TOKEN` | Trello access token. |
| `TRELLO_LIST_ID` | Trello list ID where cards will be created. |
| `GITHUB_TOKEN` | GitHub personal access token with permission to create issues. |
| `GITHUB_DEFAULT_REPO` | Default GitHub repository (`owner/repo`). |

## Commands

| Command | Description |
| --- | --- |
| `!kick @user [reason]` | Kick a member. |
| `!ban @user [reason]` | Ban a member. |
| `!unban username#1234` | Unban a member by tag. |
| `!purge [count]` | Delete the specified number of messages. |
| `!remind` | Show the server's reminders. |
| `!remind add 2024-01-01T12:00 event` | Add a reminder (UTC or with timezone). |
| `!remind remove <id>` | Remove a reminder. |
| `!sheet value1, value2` | Append a row to Google Sheets. |
| `!trello Title | Description` | Create a Trello card. |
| `!github [repo] | Title | Description` | Create a GitHub issue. |

## Integration notes

- Google Sheets requires a service account with access to the target spreadsheet.
- Trello and GitHub APIs must be enabled and tokens must have the required scopes.
- Integrations run asynchronously; errors are logged and surfaced in chat.

## Data storage

Reminders are saved to a JSON file. The file is created automatically when the first reminder is added. Ensure the bot has write access to the `data/` directory.

## Development

- To run a quick syntax check:

  ```bash
  python -m compileall bot
  ```

- The bot is modular; each area of functionality is implemented in its own cog.

Enjoy!
