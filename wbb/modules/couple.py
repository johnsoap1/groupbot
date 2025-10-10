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
import random
from datetime import datetime, timedelta
from typing import List, Tuple

import pytz
from pyrogram import enums, filters
from pyrogram.types import User

from wbb import app
from wbb.core.decorators.errors import capture_err
from wbb.utils.dbfunctions import get_couple, save_couple

__MODULE__ = "Shippering"
__HELP__ = "/detect_gay - To Choose Couple Of The Day"

# Set the timezone to Indian Standard Time
IST = pytz.timezone("Asia/Kolkata")

def get_current_ist_datetime() -> datetime:
    """Get current datetime in IST timezone."""
    return datetime.now(IST)

def get_date_strings() -> Tuple[str, str]:
    """
    Get today's and tomorrow's date strings in DD/MM/YYYY format.
    Handles month and year transitions.
    """
    today = get_current_ist_datetime()
    tomorrow = today + timedelta(days=1)
    
    today_str = today.strftime("%d/%m/%Y")
    tomorrow_str = tomorrow.strftime("%d/%m/%Y")
    
    return today_str, tomorrow_str

async def get_member_list(chat_id: int) -> List[User]:
    """Get a list of non-bot, non-deleted users in the chat."""
    members = []
    async for member in app.get_chat_members(chat_id):
        if not member.user.is_bot and not member.user.is_deleted:
            members.append(member.user)
    return members

@app.on_message(filters.command("detect_gay"))
@capture_err
async def couple(_, message):
    """Handle the /detect_gay command to select a random couple."""
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text("This command only works in groups.")

    status = await message.reply("Detecting gay among us...")
    chat_id = message.chat.id
    today_str, tomorrow_str = get_date_strings()

    try:
        # Check if a couple was already selected today
        existing_couple = await get_couple(chat_id, today_str)
        
        if existing_couple:
            # Show existing couple
            c1 = await app.get_users(existing_couple["c1_id"])
            c2 = await app.get_users(existing_couple["c2_id"])
            await status.edit(
                f"**Couple of the day:**\n"
                f"[{c1.first_name}](tg://user?id={c1.id}) + "
                f"[{c2.first_name}](tg://user?id={c2.id}) = ❤️\n\n"
                f"__New couple of the day may be chosen at 12AM {tomorrow_str}__"
            )
            return

        # Select new couple
        members = await get_member_list(chat_id)
        if len(members) < 2:
            return await status.edit("Not enough users to form a couple!")

        # Select two distinct random users
        c1, c2 = random.sample(members, 2)
        
        # Save the new couple
        couple_data = {"c1_id": c1.id, "c2_id": c2.id}
        await save_couple(chat_id, today_str, couple_data)

        # Send the result
        await status.edit(
            f"**Couple of the day:**\n"
            f"{c1.mention} + {c2.mention} = ❤️\n\n"
            f"__New couple of the day may be chosen at 12AM {tomorrow_str}__"
        )

    except Exception as e:
        await status.edit(f"An error occurred: {str(e)}")
        raise
