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


@app.on_message(filters.command(None) & ~filters.private)
async def delete_all_commands(client, message: Message):
    """
    Detects any message starting with '/', logs it, and deletes it.
    Works in all group chats where the bot has delete permissions.
    """
    # Don't process if the message is empty or doesn't have text
    if not message.text:
        return

    command_text = message.text
    chat = message.chat
    sender = message.from_user

    # Skip if the message is from the bot itself
    if sender and sender.is_self:
        return

    # Optional logging
    if LOG_COMMANDS and LOG_CHAT_ID:
        try:
            # Format the log message
            log_text = (
                f"🚫 Command deleted in {chat.title or 'a group'}\n"
                f"👤 User: {sender.mention if sender else 'Unknown'} "
                f"({sender.id if sender else 'N/A'})\n"
                f"💬 Command: `{command_text}`\n"
                f"🆔 Chat ID: `{chat.id}`"
            )
            
            # Send the log message
            await client.send_message(
                LOG_CHAT_ID,
                text=log_text,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"[Command Cleaner] Failed to log command: {e}")

    # Attempt to delete the command
    try:
        await message.delete()
    except Exception as e:
        error_msg = f"[Command Cleaner] Failed to delete command in chat {chat.id}: {e}"
        print(error_msg)
        
        # Log the error if logging is enabled
        if LOG_COMMANDS and LOG_CHAT_ID:
            try:
                await client.send_message(
                    LOG_CHAT_ID,
                    f"❌ Failed to delete command in {chat.title or 'a group'}: {str(e)[:100]}"
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
