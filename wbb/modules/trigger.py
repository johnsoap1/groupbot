"""
Trigger Module - Auto-reply with custom responses
Admins and sudoers can set global triggers that auto-reply to specific words or phrases
Supports text replies and media (photos, videos, stickers, GIFs, etc.)
"""

from pyrogram import filters, Client
from pyrogram.types import Message
from wbb import app, SUDOERS
from wbb.core.decorators import sudo_required
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from wbb.core.mongo import db

logger = logging.getLogger(__name__)

__MODULE__ = "Triggers"
__HELP__ = """
**Trigger Module**

Set automatic replies to specific words or phrases. Works globally across all groups.
Supports both text and media triggers.

**Commands:**

`/addtrigger trigger response`  - Add a text trigger with text response
`/addtrigger trigger`  (reply to media) - Add a media trigger
`/deltrigger trigger`  - Delete a trigger
`/triggers`  - List all triggers
`/cleartriggers`  - Delete all triggers (admin only)

**Examples:**

Text trigger:
`/addtrigger hello Hello there! How are you?` 

Media trigger:
(Reply to a photo with) `/addtrigger myphoto` 

**Admin and Sudoer only**
"""


class TriggerDB:
    def __init__(self):
        self.col: AsyncIOMotorCollection = db.triggers

    async def add_trigger(self, trigger: str, response: str = None, 
                         media_id: str = None, media_type: str = None):
        """Add or update a trigger"""
        trigger_lower = trigger.lower()
        await self.col.update_one(
            {"_id": trigger_lower},
            {
                "$set": {
                    "trigger": trigger,
                    "response": response,
                    "media_id": media_id,
                    "media_type": media_type,
                }
            },
            upsert=True,
        )

    async def get_trigger(self, trigger: str):
        """Get trigger details"""
        return await self.col.find_one({"_id": trigger.lower()})

    async def delete_trigger(self, trigger: str):
        """Delete a trigger"""
        await self.col.delete_one({"_id": trigger.lower()})

    async def get_all_triggers(self):
        """Get all triggers"""
        return await self.col.find({}).to_list(None)

    async def clear_all(self):
        """Clear all triggers"""
        await self.col.delete_many({})


trigger_db = TriggerDB()


async def is_admin_or_sudo(client: Client, user_id: int, chat_id: int) -> bool:
    """Check if user is admin or sudoer"""
    if user_id in SUDOERS:
        return True
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.privileges and member.privileges.can_delete_messages
    except:
        return False


@app.on_message(filters.command("addtrigger"))
async def add_trigger(client: Client, message: Message):
    """Add a new trigger"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can add triggers!")
        return

    # Check if replying to media
    if message.reply_to_message:
        reply_msg = message.reply_to_message
        
        if len(message.command) < 2:
            await message.reply_text(
                "❌ Please provide a trigger word!\n\n"
                "Usage: `/addtrigger word`  (while replying to media)"
            )
            return

        trigger = " ".join(message.command[1:])
        
        # Check what type of media is being replied to
        media_id = None
        media_type = None

        if reply_msg.photo:
            media_id = reply_msg.photo.file_id
            media_type = "photo"
        elif reply_msg.video:
            media_id = reply_msg.video.file_id
            media_type = "video"
        elif reply_msg.animation:
            media_id = reply_msg.animation.file_id
            media_type = "animation"
        elif reply_msg.sticker:
            media_id = reply_msg.sticker.file_id
            media_type = "sticker"
        elif reply_msg.document:
            media_id = reply_msg.document.file_id
            media_type = "document"
        elif reply_msg.audio:
            media_id = reply_msg.audio.file_id
            media_type = "audio"
        elif reply_msg.voice:
            media_id = reply_msg.voice.file_id
            media_type = "voice"
        else:
            await message.reply_text(
                "❌ Unsupported media type!\n\n"
                "Supported: Photo, Video, Sticker, GIF, Document, Audio, Voice"
            )
            return

        await trigger_db.add_trigger(
            trigger,
            media_id=media_id,
            media_type=media_type
        )

        await message.reply_text(
            f"✅ Media trigger added!\n\n"
            f"📌 Trigger: `{trigger}` \n"
            f"📎 Type: {media_type}"
        )

    else:
        # Text trigger
        if len(message.command) < 3:
            await message.reply_text(
                "❌ Invalid format!\n\n"
                "Usage: `/addtrigger trigger response` \n"
                "Or reply to media with `/addtrigger trigger` "
            )
            return

        trigger = message.command[1]
        response = " ".join(message.command[2:])

        await trigger_db.add_trigger(trigger, response=response)

        await message.reply_text(
            f"✅ Text trigger added!\n\n"
            f"📌 Trigger: `{trigger}` \n"
            f"💬 Response: `{response}` "
        )


@app.on_message(filters.command("deltrigger"))
async def del_trigger(client: Client, message: Message):
    """Delete a trigger"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can delete triggers!")
        return

    if len(message.command) < 2:
        await message.reply_text(
            "❌ Please specify a trigger to delete!\n\n"
            "Usage: `/deltrigger trigger_word` "
        )
        return

    trigger = " ".join(message.command[1:])
    trigger_data = await trigger_db.get_trigger(trigger)

    if not trigger_data:
        await message.reply_text(
            f"❌ Trigger `{trigger}`  not found!"
        )
        return

    await trigger_db.delete_trigger(trigger)
    await message.reply_text(
        f"✅ Trigger `{trigger}`  deleted!"
    )


@app.on_message(filters.command("triggers"))
async def list_triggers(client: Client, message: Message):
    """List all triggers"""
    
    triggers = await trigger_db.get_all_triggers()

    if not triggers:
        await message.reply_text(
            "❌ No triggers found!\n\n"
            "Use `/addtrigger`  to add triggers."
        )
        return

    text = "📋 **All Triggers:**\n\n"
    
    for i, trig in enumerate(triggers, 1):
        trigger = trig.get("trigger", "N/A")
        media_type = trig.get("media_type")
        response = trig.get("response", "")

        if media_type:
            text += f"{i}. `{trigger}`  → 📎 {media_type.upper()}\n"
        else:
            response_preview = response[:50] + "..." if len(response) > 50 else response
            text += f"{i}. `{trigger}`  → {response_preview}\n"

    await message.reply_text(text)


@app.on_message(filters.command("cleartriggers"))
async def clear_triggers(client: Client, message: Message):
    """Clear all triggers"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can clear triggers!")
        return

    triggers = await trigger_db.get_all_triggers()
    
    if not triggers:
        await message.reply_text("❌ No triggers to clear!")
        return

    await trigger_db.clear_all()
    await message.reply_text(
        f"✅ Cleared {len(triggers)} triggers!"
    )


@app.on_message(filters.text, group=100)
async def trigger_handler(client: Client, message: Message):
    """Handle trigger replies"""
    
    # Skip if message is from bot or is a command
    if message.from_user.is_bot or message.text.startswith("/"):
        return

    text = message.text.lower()
    triggers = await trigger_db.get_all_triggers()

    if not triggers:
        return

    # Check for trigger matches
    for trigger_data in triggers:
        trigger_word = trigger_data.get("trigger", "").lower()
        
        # Skip if trigger is empty
        if not trigger_word:
            continue

        # Check if trigger matches (exact word or phrase)
        if trigger_word in text:
            media_type = trigger_data.get("media_type")
            
            if media_type:
                # Media trigger
                media_id = trigger_data.get("media_id")
                
                try:
                    if media_type == "photo":
                        await message.reply_photo(media_id)
                    elif media_type == "video":
                        await message.reply_video(media_id)
                    elif media_type == "animation":
                        await message.reply_animation(media_id)
                    elif media_type == "sticker":
                        await message.reply_sticker(media_id)
                    elif media_type == "document":
                        await message.reply_document(media_id)
                    elif media_type == "audio":
                        await message.reply_audio(media_id)
                    elif media_type == "voice":
                        await message.reply_voice(media_id)
                except Exception as e:
                    logger.error(f"Error sending media trigger: {e}")
                    try:
                        await message.reply_text(
                            "⚠️ Media expired or unavailable"
                        )
                    except:
                        pass
            else:
                # Text trigger
                response = trigger_data.get("response")
                if response:
                    try:
                        await message.reply_text(response)
                    except Exception as e:
                        logger.error(f"Error sending text trigger: {e}")
            
            # Exit after first match
            break


@app.on_message(filters.media, group=99)
async def media_trigger_handler(client: Client, message: Message):
    """Handle triggers on media messages"""
    
    # Skip if message is from bot
    if message.from_user.is_bot:
        return

    # Skip if no caption
    if not message.caption:
        return

    caption = message.caption.lower()
    triggers = await trigger_db.get_all_triggers()

    if not triggers:
        return

    # Check for trigger matches in caption
    for trigger_data in triggers:
        trigger_word = trigger_data.get("trigger", "").lower()
        
        if not trigger_word:
            continue

        if trigger_word in caption:
            media_type = trigger_data.get("media_type")
            
            if media_type:
                media_id = trigger_data.get("media_id")
                
                try:
                    if media_type == "photo":
                        await message.reply_photo(media_id)
                    elif media_type == "video":
                        await message.reply_video(media_id)
                    elif media_type == "animation":
                        await message.reply_animation(media_id)
                    elif media_type == "sticker":
                        await message.reply_sticker(media_id)
                    elif media_type == "document":
                        await message.reply_document(media_id)
                    elif media_type == "audio":
                        await message.reply_audio(media_id)
                    elif media_type == "voice":
                        await message.reply_voice(media_id)
                except Exception as e:
                    logger.error(f"Error sending media trigger: {e}")
            else:
                response = trigger_data.get("response")
                if response:
                    try:
                        await message.reply_text(response)
                    except Exception as e:
                        logger.error(f"Error sending text trigger: {e}")
            
            break
