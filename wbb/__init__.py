"""
MIT License

Copyright (c) 2024 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import logging
import os
import sys
import time
from inspect import getfullargspec
from os import path
from pathlib import Path

from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pyrogram import Client, filters, __version__ as pyrogram_version
from pyrogram.types import Message
from pyromod import listen
from Python_ARQ import ARQ
from telegraph import Telegraph

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log', encoding='utf-8')
    ]
)

# Set log levels for noisy libraries
logging.getLogger('pyrogram').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("Initializing WilliamButcherBot")
logger.info(f"Python version: {sys.version}")
logger.info(f"Pyrogram version: {pyrogram_version}")
logger.info("=" * 50)

is_config = path.exists("config.py")

if is_config:
    from config import *
else:
    from sample_config import *

Path("sessions").mkdir(exist_ok=True)

USERBOT_PREFIX = USERBOT_PREFIX
GBAN_LOG_GROUP_ID = GBAN_LOG_GROUP_ID
WELCOME_DELAY_KICK_SEC = WELCOME_DELAY_KICK_SEC
LOG_GROUP_ID = LOG_GROUP_ID
MESSAGE_DUMP_CHAT = MESSAGE_DUMP_CHAT
MOD_LOAD = []
MOD_NOLOAD = []
SUDOERS = filters.user()
bot_start_time = time.time()


class Log:
    """Legacy logger for backward compatibility"""
    def __init__(self, save_to_file=False, file_name="wbb.log"):
        self.logger = logging.getLogger("wbb.legacy")
        self.save_to_file = save_to_file
        self.file_name = file_name
        if save_to_file:
            file_handler = logging.FileHandler(file_name, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

# For backward compatibility
log = Log(True, "bot.log")
logger = logging.getLogger("wbb")

# MongoDB client
log.info("Initializing MongoDB client")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client.wbb

async def load_sudoers():
    global SUDOERS
    log.info("Loading sudoers")
    sudoersdb = db.sudoers
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not sudoers else sudoers["sudoers"]
    for user_id in SUDO_USERS_ID:
        SUDOERS.add(user_id)
        if user_id not in sudoers:
            sudoers.append(user_id)
            await sudoersdb.update_one(
                {"sudo": "sudo"},
                {"$set": {"sudoers": sudoers}},
                upsert=True,
            )
    if sudoers:
        for user_id in sudoers:
            SUDOERS.add(user_id)


# Initialize app2 without starting it
app2 = None

# DeepL API Key
DEEPL_API = os.environ.get("DEEPL_API")

# Bot ID (will be set during bot startup)
BOT_ID = None

def init_userbot():
    """Initialize the userbot client"""
    global app2
    if not SESSION_STRING:
        app2 = Client(
            name="sessions/userbot",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=PHONE_NUMBER,
        )
    else:
        app2 = Client(
            name="sessions/userbot", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            session_string=SESSION_STRING
        )

aiohttpsession = ClientSession()

arq = ARQ(ARQ_API_URL, ARQ_API_KEY, aiohttpsession)

app = Client("sessions/wbb", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Global bot and userbot info variables
BOT_NAME = ""
BOT_USERNAME = ""
BOT_MENTION = ""
BOT_DC_ID = 0
USERBOT_NAME = ""
USERBOT_USERNAME = ""
USERBOT_MENTION = ""
USERBOT_DC_ID = 0

async def start_bot():
    """Start the bot and userbot clients"""
    global BOT_NAME, BOT_USERNAME, BOT_MENTION, BOT_DC_ID, BOT_ID
    global USERBOT_NAME, USERBOT_USERNAME, USERBOT_MENTION, USERBOT_DC_ID
    
    # Load sudoers first
    await load_sudoers()
    
    # Start bot
    log.info("Starting bot")
    await app.start()
    log.info("Getting bot info")
    bot_me = await app.get_me()
    BOT_NAME = bot_me.first_name + (bot_me.last_name or "")
    BOT_USERNAME = bot_me.username
    BOT_MENTION = bot_me.mention
    BOT_DC_ID = bot_me.dc_id
    BOT_ID = bot_me.id
    log.info(f"Bot started: {BOT_NAME} (@{BOT_USERNAME})")
    
    # Initialize and start userbot if needed
    global app2
    if not SESSION_STRING:
        log.info("Initializing userbot")
        app2 = init_userbot()
        log.info("Starting userbot")
        await app2.start()
        log.info("Getting userbot info")
        userbot_me = await app2.get_me()
        USERBOT_NAME = userbot_me.first_name + (userbot_me.last_name or "")
        USERBOT_USERNAME = userbot_me.username
        USERBOT_MENTION = userbot_me.mention
        USERBOT_DC_ID = userbot_me.dc_id
        log.info(f"Userbot started: {USERBOT_NAME} (@{USERBOT_USERNAME})")
        
        # Add userbot to sudoers
        if userbot_me.id not in SUDOERS:
            SUDOERS.add(userbot_me.id)
            log.info(f"Added userbot {userbot_me.id} to sudoers")
    
    log.info("Bot initialization complete")
    
    # Initialize Telegraph after we have the bot username
    init_telegraph()

# Initialize Telegraph client with a default name, will be updated after bot starts
telegraph = Telegraph(domain="graph.org")

def init_telegraph():
    """Initialize the Telegraph client with the bot's username"""
    try:
        # This will be called after the bot is started
        if BOT_USERNAME:
            telegraph.create_account(short_name=BOT_USERNAME)
            log.info(f"Initialized Telegraph client for @{BOT_USERNAME}")
        else:
            log.warning("Could not initialize Telegraph: BOT_USERNAME not set")
    except Exception as e:
        log.error(f"Failed to initialize Telegraph: {e}")


async def eor(msg: Message, **kwargs):
    func = (
        (msg.edit_text if msg.from_user.is_self else msg.reply)
        if msg.from_user
        else msg.reply
    )
    spec = getfullargspec(func.__wrapped__).args
    return await func(**{k: v for k, v in kwargs.items() if k in spec})
