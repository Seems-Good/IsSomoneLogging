import os
import json
import requests
from datetime import datetime, timezone

# ── Config from environment variables (set as GitHub Secrets) ──────────────
WCL_CLIENT_ID     = os.environ["WCL_CLIENT_ID"]
WCL_CLIENT_SECRET = os.environ["WCL_CLIENT_SECRET"]
DISCORD_WEBHOOK   = os.environ["DISCORD_WEBHOOK_URL"]
GUILD_NAME        = os.environ["GUILD_NAME"]        # e.g. "Wipe Club"
GUILD_REALM       = os.environ["GUILD_REALM"]       # e.g. "stormrage"
GUILD_REGION      = os.environ["GUILD_REGION"]      # e.g. "US"

STATE_FILE    = "last_seen.json"
LAST_LOG_FILE = "last_log.json"          # ← NEW: consumed by the status website
WCL_TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
WCL_API_URL   = "https://www.warcraftlogs.com/api/v2/client"


def get_access_token():
    """Authenticate with Warcraft Logs using client credentials."""
    resp = requests.post(
        WCL_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(WCL_CLIENT_ID, WCL_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_latest_report(token):
    """Fetch the most recent report for the guild."""
    query = """
    query($guildName: String!, $realm: String!, $region: String!) {
      reportData {
        reports(
          guildName: $guildName
          guildServerSlug: $realm
          guildServerRegion: $region
          limit: 1
        ) {
          data {
            code
            title
            startTime
            owner { name }
            zone { name }
          }
        }
      }
    }
    """
    resp = requests.post(
        WCL_API_URL,
        json={
            "query": query,
            "variables": {
                "guildName": GUILD_NAME,
                "realm": GUILD_REALM,
                "region": GUILD_REGION,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    reports = data["data"]["reportData"]["reports"]["data"]
    return reports[0] if reports else None


def load_last_seen():
    """Load the last seen report code from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f).get("last_code")
    return None


def save_last_seen(code):
    """Save the latest report code to the state file."""
    with open(STATE_FILE, "w") as f:
        json.dump({"last_code": code}, f)


# ── NEW: write last_log.json so the status website can read it ─────────────
def save_last_log(report):
    """
    Write a small JSON file that the static status website fetches.
    Committed to the repo so it's accessible via raw.githubusercontent.com.
    """
    payload = {
        "code":      report["code"],
        "title":     report.get("title") or "Untitled Report",
        "zone":      report.get("zone", {}).get("name", "Unknown Zone"),
        "owner":     report.get("owner", {}).get("name", "Unknown"),
        "startTime": report["startTime"],   # milliseconds UTC, from WCL
        "url":       f"https://www.warcraftlogs.com/reports/{report['code']}",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    with open(LAST_LOG_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"📝 last_log.json updated → {payload['title']} ({payload['zone']})")
# ───────────────────────────────────────────────────────────────────────────


def send_discord_notification(report):
    """Post a Discord embed with the new log details."""
    upload_time   = datetime.fromtimestamp(report["startTime"] / 1000, tz=timezone.utc)
    formatted_time = upload_time.strftime("%A, %B %d %Y at %H:%M UTC")

    log_url = f"https://www.warcraftlogs.com/reports/{report['code']}"
    zone    = report.get("zone", {}).get("name", "Unknown Zone")
    owner   = report.get("owner", {}).get("name", "Unknown")
    title   = report.get("title") or "Untitled Report"

    embed = {
        "title": "📋 New Warcraft Log Uploaded",
        "url": log_url,
        "color": 0xFF7C00,
        "fields": [
            {"name": "📅 Date / Time", "value": formatted_time,             "inline": False},
            {"name": "🗺️ Zone",        "value": zone,                       "inline": True},
            {"name": "👤 Uploaded by", "value": owner,                      "inline": True},
            {"name": "🔗 Report",      "value": f"[View Log]({log_url})",   "inline": False},
        ],
        "footer": {"text": f"Guild: {GUILD_NAME} • {GUILD_REGION.upper()}-{GUILD_REALM.title()}"},
    }

    resp = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=15)
    resp.raise_for_status()
    print(f"✅ Discord notification sent for report {report['code']}")


def main():
    print("Checking Warcraft Logs for new reports...")

    token  = get_access_token()
    report = get_latest_report(token)

    if not report:
        print("No reports found for this guild.")
        return

    latest_code = report["code"]
    last_code   = load_last_seen()

    print(f"Latest report : {latest_code}")
    print(f"Last seen     : {last_code or '(first run)'}")

    save_last_log(report)  # ← always write, regardless of whether it's new

    if last_code is None:
        print("First run — saving current report. Will notify on next new upload.")
        save_last_seen(latest_code)
        return

    if latest_code == last_code:
        print("No new reports. Nothing to do.")
        return

    # New report found!
    send_discord_notification(report)
    save_last_seen(latest_code)


if __name__ == "__main__":
    main()
