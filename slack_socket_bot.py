import os
import re
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import ticket
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")   # Bot token (starts with xoxb-)
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")   # App-level token (starts with xapp-)
ALLOWED_BOT_IDS = str(os.getenv("ALLOWED_BOT_IDS")).split(",")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    logger.error("Environment variables SLACK_BOT_TOKEN and SLACK_APP_TOKEN are not set.")
    exit(1)

app = App(token=SLACK_BOT_TOKEN)

USER_MENTION_RE = re.compile(r"<@([A-Z0-9]+)>", re.I)

def resolve_user_name(user_id):
    try:
        resp = app.client.users_info(user=user_id)
        if resp.get("ok"):
            profile = resp["user"]["profile"]
            return profile.get("display_name") or profile.get("real_name") or resp["user"].get("name")
    except Exception as e:
        logger.warning(f"It was not possible to resolve the name of {user_id}: {e}")
    return user_id

def parse_key_values(text):
    pattern = re.compile(r"\*(?P<key>[^*]+):\*\s*(?P<value>.*?)(?=(\*\w+?:\*)|$)", re.S)
    result = {}
    for match in pattern.finditer(text):
        key = match.group("key").strip()
        value = match.group("value").strip()
        if key and value:
            result[key] = value
    return result

@app.message("")
def handle_message(message, logger):
    """
    Triggered every time a new message is posted in a channel
    where the bot is a member.
    """
    bot_id = message.get("bot_id")
    if bot_id not in ALLOWED_BOT_IDS:
        return
    
    text = message.get("text", "") or ""

    mention_ids = USER_MENTION_RE.findall(text)
    for uid in mention_ids:
        name = resolve_user_name(uid)
        text = text.replace(f"<@{uid}>", f"@{name}")

    parsed_fields = parse_key_values(text)
    informador = parsed_fields.get("Informador", "").replace("@", "").strip() or "Desconhecido"
    
    info = {
        "message_text": text.encode("utf-8", errors="ignore").decode("utf-8"),
        "timestamp": message.get("ts", ""),
        "user": informador,
        "parsed_fields": parsed_fields
    }
    tk = ticket.Ticket(logger=logger, info=info)
    tk.create(customer="Metlife")

if __name__ == "__main__":
    print("⚡ Starting Slack bot using Socket Mode...")
    try:
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    except Exception as e:
        logger.error(f"Failed to start Slack bot: {e}")
