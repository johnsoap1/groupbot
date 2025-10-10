from pyrogram import filters
from pyrogram.types import Message
from wbb import SUDOERS, USERBOT_PREFIX, app, app2

__MODULE__ = "Dice"
__HELP__ = """
/dice
    Roll a dice.
"""

# Safe userbot decorator
def userbot_on_message(*args, **kwargs):
    if app2:
        return app2.on_message(*args, **kwargs)
    # Dummy decorator if userbot is not initialized
    def dummy(func):
        return func
    return dummy


@userbot_on_message(
    filters.command("dice", prefixes=USERBOT_PREFIX)
    & SUDOERS
    & ~filters.forwarded
    & ~filters.via_bot
)
@app.on_message(filters.command("dice"))
async def throw_dice(client, message: Message):
    # Check if sender is sudo
    is_sudo = message.from_user.id in SUDOERS if message.from_user else False
    chat_id = message.chat.id

    # Normal dice roll
    if not is_sudo:
        await client.send_dice(chat_id, "🎲")
        return

    # Keep rolling until 6 if sudo
    dice_msg = await client.send_dice(chat_id, "🎲")
    while dice_msg.dice.value != 6:
        await dice_msg.delete()
        dice_msg = await client.send_dice(chat_id, "🎲")
