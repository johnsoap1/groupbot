"""
Command Cleaner Module
Automatically deletes all commands (messages starting with /) in group chats.

This module will detect and delete any command message in any group chat
where the bot has delete message permissions.
"""
from pyrogram import filters
from pyrogram.types import Message

from wbb import app, LOG_GROUP_ID

# Configuration
LOG_COMMANDS = True  # Set to False to disable command logging
LOG_CHAT_ID = LOG_GROUP_ID  # Uses the bot's log group by default

@app.on_message(~filters.private)
async def delete_commands(client, message: Message):
    """Delete command messages in groups"""
    try:
        # Skip if the message is from a bot or not a text message
        if not message.text or (message.from_user and message.from_user.is_bot):
            return
            
        # Check if message starts with a command
        if not message.text.startswith('/'):
            return
            
        # Delete the command message
        await message.delete()
        
        # Log the deleted command if logging is enabled
        if LOG_COMMANDS and LOG_CHAT_ID:
            log_text = (
                f"Deleted command in {message.chat.title} (ID: {message.chat.id})\n"
                f"User: {message.from_user.mention if message.from_user else 'Unknown'}"
                f" (ID: {message.from_user.id if message.from_user else 'N/A'})\n"
                f"Command: {message.text}\n"
            )
            
            # Send log to the log chat
            await app.send_message(
                chat_id=LOG_CHAT_ID,
                text=log_text,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        # Log any errors but don't crash the handler
        if LOG_CHAT_ID:
            try:
                await app.send_message(
                    chat_id=LOG_CHAT_ID,
                    text=f"❌ Error in command_cleaner: {str(e)[:300]}"
                )
            except Exception as log_err:
                print(f"[Command Cleaner] Failed to log error: {log_err}")


__MODULE__ = "Command Cleaner"
__HELP__ = """
**Command Cleaner Module**

This module automatically deletes all command messages (starting with /) in group chats.

**Features:**
- Deletes any command message in any group chat
- Works for all users, including admins
- Logs deleted commands to the log group
- Respects bot's delete message permissions

**Note:** The bot needs 'Delete Messages' permission in the chat for this to work.
"""
