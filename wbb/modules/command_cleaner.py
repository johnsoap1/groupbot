"""
Command Cleaner Module
Automatically deletes all commands (messages starting with /) in group chats.

Features:
- Detects and deletes any command message in any group chat
- Works with commands that have mentions (e.g., /start@botname)
- Optional command logging with detailed information
- Configurable log chat and command whitelist
- Proper error handling and permission checks
"""

from pyrogram import filters
from pyrogram.types import Message
from typing import Dict, List, Optional, Union
import re

from wbb import app, LOG_GROUP_ID

# Configuration
LOG_COMMANDS = True  # Set to False to disable command logging
LOG_CHAT_ID = LOG_GROUP_ID  # Uses the bot's log group by default
COMMAND_PATTERN = re.compile(r"^/([a-zA-Z0-9_]+)(@\w+)?(\s|$)")  # Matches /command or /command@botname

# List of commands to ignore (case-insensitive)
WHITELISTED_COMMANDS = ["start", "help", "settings"]

def is_command(text: str) -> bool:
    """Check if the given text is a command."""
    if not text or not text.startswith('/'):
        return False
    
    # Check if it's a command by pattern matching
    match = COMMAND_PATTERN.match(text)
    if not match:
        return False
    
    # Extract the command name (without the slash)
    command = match.group(1).lower() if match.group(1) else ""
    return command not in WHITELISTED_COMMANDS

async def log_command_deletion(message: Message, command: str):
    """Log the deleted command to the log chat."""
    if not LOG_COMMANDS or not LOG_CHAT_ID:
        return

    try:
        chat = message.chat
        user = message.from_user
        
        log_text = (
            "🗑 **Command Deleted**\n\n"
            f"**Chat:** {chat.title if chat.title else 'N/A'} "
            f"(`{chat.id}`)\n"
            f"**User:** {user.mention if user else 'N/A'} "
            f"(`{user.id if user else 'N/A'}`)\n"
            f"**Command:** `{command}`\n"
        )
        
        if message.reply_to_message:
            log_text += f"**Replied to:** [Message]({message.link}) by "
            if message.reply_to_message.from_user:
                log_text += f"{message.reply_to_message.from_user.mention} "
                log_text += f"(`{message.reply_to_message.from_user.id}`)\n"
            else:
                log_text += "Unknown user\n"
        
        await app.send_message(
            chat_id=LOG_CHAT_ID,
            text=log_text,
            disable_web_page_preview=True
        )
    except Exception as e:
        # Don't crash if logging fails
        print(f"Error logging command deletion: {e}")

@app.on_message(filters.group & ~filters.private & ~filters.service)
async def command_cleaner_handler(_, message: Message):
    """Handle command messages in groups and delete them."""
    try:
        # Skip if the message is not a text message or is from a bot
        if not message.text or (message.from_user and message.from_user.is_bot):
            return
            
        # Check if it's a command and not whitelisted
        if not is_command(message.text):
            return
            
        # Check if we have permission to delete messages
        if not await can_delete_messages(message):
            return
            
        # Delete the command message
        await message.delete()
        
        # Log the deleted command
        await log_command_deletion(message, message.text.split()[0])
            
    except Exception as e:
        # Log any errors but don't crash the handler
        error_msg = f"Error in command_cleaner: {str(e)}"
        if LOG_CHAT_ID:
            try:
                await app.send_message(LOG_CHAT_ID, error_msg[:300])
            except:
                pass

async def can_delete_messages(message: Message) -> bool:
    """Check if the bot has permission to delete messages in the chat."""
    try:
        # Check bot's permissions in the chat
        chat_member = await message.chat.get_member("me")
        return chat_member.can_delete_messages if chat_member else False
    except Exception:
        return False

__MODULE__ = "Command Cleaner"
__HELP__ = """
**Command Cleaner Module**

This module automatically deletes command messages in group chats to keep chats clean.

**Features:**
- Automatically deletes any command message (starting with /)
- Ignores whitelisted commands like /start and /help
- Logs deleted commands to the log group
- Respects bot permissions

**Configuration:**
- `LOG_COMMANDS`: Set to False to disable command logging
- `WHITELISTED_COMMANDS`: List of commands that won't be deleted
- `LOG_CHAT_ID`: The chat ID where logs will be sent

**Note:** The bot needs 'Delete Messages' admin rights in groups to work properly.
"""
