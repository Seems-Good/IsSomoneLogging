# IsSomoneLogging

> GitHub Action that polls the Warcraft Logs API on raid nights and pings Discord if a new log has been uploaded.

![Status](https://github.com/Seems-Good/IsSomoneLogging/actions/workflows/checklogs.yml/badge.svg)
![Last Run](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Seems-Good/IsSomoneLogging/main/last_run_badge.json)
![Next Run](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Seems-Good/IsSomoneLogging/main/next_run_badge.json)

## How it works

Every 5 minutes during raid windows (8pm–11pm ET on Tuesday, Thursday, and Sunday), this action:

1. Authenticates with the Warcraft Logs API
2. Fetches the most recent report for the guild
3. Compares it against the last seen report code
4. Sends a Discord notification if a new log was uploaded
5. Updates the last run / next run badges above

## Secrets required

| Secret | Description |
|---|---|
| `WCL_CLIENT_ID` | Warcraft Logs API client ID |
| `WCL_CLIENT_SECRET` | Warcraft Logs API client secret |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL |
| `GUILD_NAME` | Guild name (e.g. `Seems Good`) |
| `GUILD_REALM` | Realm slug (e.g. `stormrage`) |
| `GUILD_REGION` | Region (e.g. `US`) |
