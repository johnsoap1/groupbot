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
from pathlib import Path

from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pyrogram import Client, filters, __version__ as pyrogram_version
from pyrogram.types import Message
from pyromod import listen
from Python_ARQ import ARQ
from telegraph import Telegraph

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("wbb")

# Set log levels for noisy libraries
logging.getLogger('pyrogram').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Create sessions folder
Path("sessions").mkdir(exist_ok=True)

# Load configuration
try:
    from config import *
    logger.info("Loaded configuration from config.py")
except ImportError:
    from sample_config import *
    logger.info("Loaded configuration from sample_config.py")

# Global variables
USERBOT_PREFIX = USERBOT_PREFIX
GBAN_LOG_GROUP_ID = GBAN_LOG_GROUP_ID
WELCOME_DELAY_KICK_SEC = WELCOME_DELAY_KICK_SEC
LOG_GROUP_ID = LOG_GROUP_ID
MESSAGE_DUMP_CHAT = MESSAGE_DUMP_CHAT
MOD_LOAD = []
MOD_NOLOAD = []
SUDOERS = filters.user()
bot_start_time = time.time()

# MongoDB connection
mongo_client = MongoClient(MONGO_URL)
db = mongo_client.wbb

async def load_sudoers():
    """Load sudo users from database"""
    global SUDOERS
    logger.info("Loading sudoers")
    sudoersdb = db.sudoers
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not sudoers else sudoers["sudoers"]
    
    # Add users from config to sudoers
    for user_id in SUDO_USERS_ID:
        SUDOERS.add(user_id)
        if user_id not in sudoers:
            sudoers.append(user_id)
            await sudoersdb.update_one(
                {"sudo": "sudo"},
                {"$set": {"sudoers": sudoers}},
                upsert=True,
            )
    
    # Add all sudoers to SUDOERS set
    for user_id in sudoers:
        SUDOERS.add(user_id)
    
    logger.info(f"Loaded {len(SUDOERS)} sudoers")

# Initialize Pyrogram clients
app = None
app2 = None

# Initialize main bot client
try:
    app = Client("sessions/wbb", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
    logger.info("Main bot client initialized")
except Exception as e:
    logger.error(f"Failed to initialize main bot client: {e}")
    app = None

# Initialize userbot client if SESSION_STRING is provided
if SESSION_STRING:
    try:
        app2 = Client(
            "sessions/userbot",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING
        )
        logger.info("Userbot client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize userbot client: {e}")
        app2 = None
else:
    logger.info("No SESSION_STRING provided, userbot disabled")

# Global bot and userbot info variables
BOT_NAME = BOT_USERNAME = BOT_MENTION = ""
BOT_DC_ID = BOT_ID = 0
USERBOT_NAME = USERBOT_USERNAME = USERBOT_MENTION = ""
USERBOT_DC_ID = USERBOT_ID = 0

# Initialize ARQ client
aiohttpsession = ClientSession()
arq = ARQ(ARQ_API_URL, ARQ_API_KEY, aiohttpsession)

# Initialize Telegraph client (will be configured after bot starts)
telegraph = Telegraph(domain="graph.org")

def userbot_on_message(*args, **kwargs):
    """Safe decorator for userbot message handlers.
    
    This ensures that @app2.on_message handlers don't break if userbot is not available.
    
    Usage:
        @userbot_on_message(filters.command("start"))
        async def start(_, message):
            await message.reply("Hello from userbot!")
    """
    if app2:
        return app2.on_message(*args, **kwargs)
    
    # Return a dummy decorator if userbot is not available
    def decorator(func):
        return func
    return decorator

async def start_bot():
    """Start the bot and userbot clients"""
    global BOT_NAME, BOT_USERNAME, BOT_MENTION, BOT_DC_ID, BOT_ID
    global USERBOT_NAME, USERBOT_USERNAME, USERBOT_MENTION, USERBOT_DC_ID, USERBOT_ID
    
    # Load sudoers first
    await load_sudoers()
    
    # Start main bot
    if app is None:
        logger.error("Cannot start: Main bot client is not initialized")
        return False
        
    try:
        logger.info("Starting main bot...")
        await app.start()
        
        # Get bot info
        me = await app.get_me()
        BOT_NAME = me.first_name + (" " + me.last_name if me.last_name else "")
        BOT_USERNAME = me.username
        BOT_MENTION = me.mention
        BOT_DC_ID = me.dc_id
        BOT_ID = me.id
        
        logger.info(f"Bot started: {BOT_NAME} (@{BOT_USERNAME})")
    except Exception as e:
        logger.error(f"Failed to start main bot: {e}")
        return False
    
    # Start userbot if available
    if app2 is not None:
        try:
            logger.info("Starting userbot...")
            await app2.start()
            
            # Get userbot info
            me2 = await app2.get_me()
            USERBOT_NAME = me2.first_name + (" " + me2.last_name if me2.last_name else "")
            USERBOT_USERNAME = me2.username
            USERBOT_MENTION = me2.mention
            USERBOT_DC_ID = me2.dc_id
            USERBOT_ID = me2.id
            
            logger.info(f"Userbot started: {USERBOT_NAME} (@{USERBOT_USERNAME})")
        except Exception as e:
            logger.error(f"Failed to start userbot: {e}")
            app2 = None
    
    # Initialize Telegraph with bot username if available
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
