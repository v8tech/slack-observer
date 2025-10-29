import os
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import ticket

# -------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Slack Token Configuration
# -------------------------------------------------------------------

# It's strongly recommended to store your tokens in environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")   # Bot token (starts with xoxb-)
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")   # App-level token (starts with xapp-)

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    logger.error("Environment variables SLACK_BOT_TOKEN and SLACK_APP_TOKEN are not set.")
    exit(1)

# Initialize Slack Bolt app
app = App(token=SLACK_BOT_TOKEN)

# -------------------------------------------------------------------
# Message Event Listener
# -------------------------------------------------------------------

@app.message("")
def handle_message(message, logger):
    """
    Triggered every time a new message is posted in a channel
    where the bot is a member.
    """
    info = {}
    try:
        info["channel_id"] = message.get("channel", "N/A")
        info["message_text"] = message.get("text", "")
        info["timestamp"] = message.get("ts", "")
        info["user"] = message.get("user", "N/A")
        info["bot_id"] = message.get("bot_id", "N/A")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

    tk = ticket.Ticket(logger=logger, info=info)
    tk.create(customer="")
        

# -------------------------------------------------------------------
# Start the Slack App
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("⚡ Starting Slack bot using Socket Mode...")
    try:
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    except Exception as e:
        logger.error(f"Failed to start Slack bot: {e}")
