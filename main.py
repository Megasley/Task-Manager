import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import threading
from flask import Flask, request, jsonify
import asyncio
from datetime import datetime

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Flask setup for webhook
app = Flask(__name__)

# Channel ID where the bot will send messages
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))

# User IDs as a dictionary loaded from environment variables
USER_ID = {
    'EM': os.environ.get('USER_ID_EM'),
    'Sarah White': os.environ.get('USER_ID_SARAH_WHITE'),
    'Megasley': os.environ.get('USER_ID_MEGASLEY'),
    'Yami': os.environ.get('USER_ID_YAMI'),
    'Satoshee': os.environ.get('USER_ID_SATOSHEE'),
    'Orion': os.environ.get('USER_ID_ORION')
}

@app.route('/')
def index():
    return "Bot is Alive"

@app.route('/www', methods=['POST'])
def www():
    data = request.get_json()

    for task in data['tasks']:
        name = task['accountable']
        mention = USER_ID.get(name, 'Unknown User')  # Use the dictionary directly

        message = f"""
**WWW Task Notification** 🔔

Hey {mention}, you have an overdue task on WWW sheet.

***Task:*** {task['task']}
***Due date:*** {task['due']}
***Status:*** {task['status']}

Please complete the task as soon as possible.
"""
        asyncio.run_coroutine_threadsafe(send_to_discord(message), bot.loop)

    return jsonify({"status": "success", "message": "Webhook received"}), 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    entry_date = data['columnData']['col5']

    message = f"""
------------------------------- 
**Feedback Task Assigned** 📋

***Row:*** **{data['row']}**
***Assigned to:*** {data['new']}
***Feedback:*** {data['columnData']['col1']}
***Source:*** {data['columnData']['col3']}
***Entry Date:*** {datetime.strptime(entry_date, "%Y-%m-%dT%H:%M:%S.%fZ").date()}
    """
    asyncio.run_coroutine_threadsafe(send_to_discord(message), bot.loop)

    return jsonify({"status": "success", "message": "Webhook received"}), 200


@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()

    name = data['columnData']['accountable']
    task = data['columnData']['task']
    old_status = data['old']
    new_status = data['new']
    due = data['columnData']['due']

    mention = USER_ID.get(name, 'Unknown User')  # Use the dictionary directly

    if new_status == 'Ready for review':
        message = f"""
-------------------------------
**Task Status Changed** !

Hey {USER_ID['Sarah White']} there's a task waiting for you to review.

***Task:*** {task}
***Due:*** {datetime.strptime(due, "%Y-%m-%dT%H:%M:%S.%fZ").date()}
***Accountable:*** {mention}
        """
    else:
        message = f"""
-------------------------------
*Task Status Changed from* **{old_status}** *to* **{new_status}** 🚀

***Task:*** {task}
***Due:*** {datetime.strptime(due, "%Y-%m-%dT%H:%M:%S.%fZ").date()}
***Accountable:*** {mention}
        """

    asyncio.run_coroutine_threadsafe(send_to_discord(message), bot.loop)

    return jsonify({"status": "success", "message": "Webhook received"}), 200


@app.route('/comment', methods=['POST'])
def comment():
    data = request.get_json()

    name = data['columnData']['accountable']
    task = data['columnData']['task']
    comment = data['new']
    due = data['columnData']['due']
    status = data['columnData']['status']
    sarah_comment = data['columnData']['sarahComment']
    member_comment = data['columnData']['memberComment']

    mention = USER_ID.get(name, 'Unknown User')  # Use the dictionary directly

    if comment == sarah_comment:
        message = f"""
-------------------------------
*{USER_ID['Sarah White']} added a comment for {mention}* 💬

***Task:*** {task}
***Status:*** {status}
***Sarah's Comment:*** {sarah_comment}
***{name}'s Comment:*** {member_comment}
***Due:*** {datetime.strptime(due, "%Y-%m-%dT%H:%M:%S.%fZ").date()}
***Accountable:*** {mention}
        """

    else:
        message = f"""
-------------------------------
*{mention} added a comment for {USER_ID['Sarah White']}* 💬

***Task:*** {task}
***Sarah's Comment:*** {sarah_comment}
***{name}'s Comment:*** {member_comment}
***Due:*** {datetime.strptime(due, "%Y-%m-%dT%H:%M:%S.%fZ").date()}
***Accountable:*** {mention}
        """

    asyncio.run_coroutine_threadsafe(send_to_discord(message), bot.loop)

    return jsonify({"status": "success", "message": "Webhook received"}), 200


async def send_to_discord(message):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)


def run_flask():
    app.run(host='0.0.0.0', port=5000)


def keep_alive():
    threading.Thread(target=run_flask).start()


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command(name='send')
async def send_message(ctx, *, message):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)
        await ctx.send(f"Message sent to <#{CHANNEL_ID}>")
    else:
        await ctx.send("Error: Couldn't find the specified channel.")


if __name__ == '__main__':
    keep_alive()  # Start the Flask server and keep it alive
    bot.run(os.environ.get('BOT_TOKEN'))  # Start the Discord bot
