# Slack Message Fetcher & Listener

This repository contains **two example Python scripts** that demonstrate how to interact with the **Slack API** to retrieve and process messages from channels.

You can use them as a base for analytics, automation, or message monitoring inside your Slack workspace.

---

## 📜 Overview

| Script                       | Description                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| **`fetch_slack_history.py`** | Fetches **past (historical)** messages from a specific Slack channel.                 |
| **`slack_socket_bot.py`**    | Listens to **new (real-time)** messages posted in channels where the bot is a member. |

These examples can be adapted for many use cases — such as building analytics dashboards, chat archivers, or automation tools.

---

## ⚙️ Requirements

* Python **3.9+**
* A Slack workspace where you can create and install an app
* The following libraries (already listed in `requirements.txt`):

  ```
  slack-sdk
  slack-bolt
  ```

---

## 🚀 1. Set up your Slack App

You’ll need to create a **Slack App** and connect it to your workspace.

### Step-by-step:

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click **"Create New App"**.

2. Choose **"From scratch"**, give it a name (e.g. `MessageFetcherBot`), and select your workspace.

3. In the sidebar, open **"OAuth & Permissions"** and add these **Bot Token Scopes**:

   ```
   channels:history
   channels:read
   chat:write
   app_mentions:read
   im:history
   im:read
   groups:history
   groups:read
   ```

4. Scroll down and click **"Install App to Workspace"**.
   This will generate a **Bot User OAuth Token** (starts with `xoxb-`).

5. In the sidebar, go to **"Socket Mode"** and **enable it**.
   Then, create an **App-Level Token** (starts with `xapp-`) with the permission:

   ```
   connections:write
   ```

6. Copy both tokens — you’ll need them for your environment variables.

7. Finally, **invite your bot to the channel** you want to read messages from:

   ```
   /invite @your-bot-name
   ```

---

## 🔑 2. Configure environment variables

Create a `.env` file or set the variables in your terminal:

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_APP_TOKEN="xapp-your-app-token-here"
```

You can also load them from a `.env` file using tools like `python-dotenv` (optional).

---

## 💻 3. Install dependencies

Install the required libraries from `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🕓 4. Run the scripts

### ▶️ Fetch past messages (historical data)

Use the script **`fetch_slack_history.py`** to download messages from a specific channel:

```bash
python fetch_slack_history.py
```

This script retrieves messages **that were already sent** in the channel and prints them in the terminal.
You can easily modify it to save them to a JSON or database for further analysis.

---

### ⚡ Listen to new messages in real-time

Use **`slack_socket_bot.py`** to start a live listener that reacts to **new incoming messages**:

```bash
python slack_socket_bot.py
```

The script uses **Slack Socket Mode**, which keeps a live WebSocket connection open and triggers your function every time a new message arrives.

---

## 🧩 5. Example output

```
------------------------------------------------------------
Channel:   C08FNQR0N3E
User:      U123456789
Message:   Hello world!
Timestamp: 1729347856.000200
------------------------------------------------------------
```

---

## 🛠️ Customization ideas

Both scripts are **starting points** — you can easily adapt them to:

* Store messages in a database (e.g., SQLite, PostgreSQL)
* Perform sentiment analysis or keyword detection
* Build dashboards of Slack activity
* Automate responses or workflows
* Integrate Slack messages with other systems (CRM, analytics tools, etc.)

---

## ⚠️ Notes

* **Never commit your Slack tokens** to a public repository.
  Always use environment variables.
* If your bot doesn’t receive messages, ensure it has been **invited** to the channel and the required **scopes** are set.
* Slack’s free plan limits message history — older messages may not be accessible.

---

## 📚 References

* [Slack API Documentation](https://api.slack.com/)
* [Slack Bolt for Python](https://slack.dev/bolt-python)
* [Slack Web API (slack_sdk)](https://slack.dev/python-slack-sdk/web/index.html)
