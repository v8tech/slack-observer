import os
import time
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# -------------------------------------------------------------------
# Configuration and Setup
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load Slack token from environment variable (safer than hardcoding)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    logging.error("Environment variable SLACK_BOT_TOKEN is not set.")
    exit(1)

client = WebClient(token=SLACK_BOT_TOKEN)

# -------------------------------------------------------------------
# Function to fetch channel message history
# -------------------------------------------------------------------

def fetch_channel_history(channel_id: str, limit: int = 1000):
    """
    Fetches the message history of a Slack channel with pagination.

    Args:
        channel_id (str): Channel ID (e.g., "C012AB3CDE").
        limit (int): Maximum number of messages to retrieve.

    Returns:
        list[dict]: List of message objects.
    """
    all_messages = []
    cursor = None

    logging.info(f"Fetching message history for channel {channel_id}...")

    try:
        while len(all_messages) < limit:
            response = client.conversations_history(
                channel=channel_id,
                limit=min(200, limit - len(all_messages)),
                cursor=cursor
            )

            messages = response.get("messages", [])
            if not messages:
                break

            all_messages.extend(messages)
            logging.info(f"Fetched {len(all_messages)} messages so far...")

            if not response.get("has_more"):
                break

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

            # Optional: avoid hitting Slack rate limits
            time.sleep(1)

        logging.info(f"Done! Retrieved {len(all_messages)} messages total.")
        return all_messages

    except SlackApiError as e:
        error_msg = e.response.get("error", "unknown_error")
        logging.error(f"Error fetching history for channel {channel_id}: {error_msg}")
        return []

# -------------------------------------------------------------------
# Main Script
# -------------------------------------------------------------------

if __name__ == "__main__":
    TARGET_CHANNEL_ID = "CHAR"  # Replace with your channel ID

    messages = fetch_channel_history(TARGET_CHANNEL_ID)

    if not messages:
        logging.warning("No messages retrieved.")
        exit(0)

    # Display messages from oldest to newest
    for msg in reversed(messages):
        print("-" * 60)
        print(f"Channel:   {TARGET_CHANNEL_ID}")
        print(f"User:      {msg.get('user', 'N/A')}")
        print(f"Bot ID:    {msg.get('bot_id', 'N/A')}")
        print(f"Message:   {msg.get('text', '')}")
        print(f"Timestamp: {msg.get('ts', '')}")
        print("-" * 60 + "\n")
