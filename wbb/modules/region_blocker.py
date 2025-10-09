"""
Region Blocker Module - Block users by country and language/script
Helps prevent spam, bot attacks, and DDoS-like behavior
Admins can block specific countries and language scripts
"""

from pyrogram import filters, Client
from pyrogram.types import Message, ChatMember
from wbb import app, SUDOERS
import logging
from motor.motor_asyncio import AsyncMotorCollection
from wbb.core.mongo import db
import re

logger = logging.getLogger(__name__)

__MODULE__ = "Region Blocker"
__HELP__ = """
**Region Blocker Module**

Block users by country or language/script. Automatically kicks users from blocked regions.
Helps prevent spam, bot networks, and targeted attacks.

**Commands:**

`/block country1,country2,...`  - Block specific countries
`/blocklang script1,script2,...`  - Block specific language scripts
`/unblock country1,country2,...`  - Unblock specific countries
`/unblocklang script1,script2,...`  - Unblock language scripts
`/blocklist`  - View blocked countries and languages
`/clearblocklist`  - Clear all blocks (admin only)

**Supported Countries:**
india, china, russia, iran, north_korea, pakistan, bangladesh, 
vietnam, thailand, indonesia, ukraine, belarus, etc.

**Supported Language Scripts:**
cyrillic (Russian, Ukrainian, Serbian, Bulgarian)
arabic (Arabic dialects)
hindi (Devanagari script - Hindi, Marathi, Sanskrit)
chinese (Simplified and Traditional Chinese)
thai (Thai script)
korean (Hangul - Korean)
persian (Persian/Farsi)
hebrew (Hebrew)
georgian (Georgian)
mongolian (Mongolian)

**Examples:**

`/block china,russia,iran`  - Block users from these countries
`/blocklang cyrillic,arabic`  - Block Cyrillic and Arabic scripts
`/blocklist`  - Show all current blocks
`/unblock russia`  - Unblock Russia

**Admin only**
"""


# Language script patterns
LANGUAGE_SCRIPTS = {
    "cyrillic": {
        "pattern": r"[\u0400-\u04FF]",
        "description": "Cyrillic (Russian, Ukrainian, Serbian, Bulgarian)"
    },
    "arabic": {
        "pattern": r"[\u0600-\u06FF\u0750-\u077F]",
        "description": "Arabic"
    },
    "hebrew": {
        "pattern": r"[\u0590-\u05FF]",
        "description": "Hebrew"
    },
    "hindi": {
        "pattern": r"[\u0900-\u097F]",
        "description": "Hindi/Devanagari (Hindi, Marathi, Sanskrit)"
    },
    "chinese": {
        "pattern": r"[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF]",
        "description": "Chinese (Simplified and Traditional)"
    },
    "thai": {
        "pattern": r"[\u0E00-\u0E7F]",
        "description": "Thai"
    },
    "korean": {
        "pattern": r"[\uAC00-\uD7AF\u1100-\u11FF]",
        "description": "Korean (Hangul)"
    },
    "persian": {
        "pattern": r"[\u0600-\u06FF]",
        "description": "Persian/Farsi"
    },
    "georgian": {
        "pattern": r"[\u10A0-\u10FF]",
        "description": "Georgian"
    },
    "mongolian": {
        "pattern": r"[\u1800-\u18AF]",
        "description": "Mongolian"
    }
}

# Country code mapping
COUNTRY_CODES = {
    "india": ["IN", "भ", "India"],
    "china": ["CN", "中", "China", "台灣", "Taiwan"],
    "russia": ["RU", "РУ", "Russia"],
    "iran": ["IR", "ایران", "Iran"],
    "north_korea": ["KP", "North Korea", "DPRK"],
    "pakistan": ["PK", "Pakistan"],
    "bangladesh": ["BD", "Bangladesh"],
    "vietnam": ["VN", "Vietnam"],
    "thailand": ["TH", "Thailand"],
    "indonesia": ["ID", "Indonesia"],
    "ukraine": ["UA", "УК", "Ukraine"],
    "belarus": ["BY", "БЕ", "Belarus"],
    "myanmar": ["MM", "Myanmar", "Burma"],
    "cambodia": ["KH", "Cambodia"],
    "laos": ["LA", "Laos"],
    "philippines": ["PH", "Philippines"],
    "malaysia": ["MY", "Malaysia"],
    "singapore": ["SG", "Singapore"],
    "hong_kong": ["HK", "Hong Kong"],
    "macao": ["MO", "Macao"],
    "south_korea": ["KR", "South Korea"],
    "japan": ["JP", "Japan"],
    "egypt": ["EG", "مصر", "Egypt"],
    "saudi_arabia": ["SA", "السعودية", "Saudi Arabia"],
    "uae": ["AE", "الإمارات", "UAE"],
    "iraq": ["IQ", "العراق", "Iraq"],
    "syria": ["SY", "سوريا", "Syria"],
    "lebanon": ["LB", "لبنان", "Lebanon"],
    "yemen": ["YE", "اليمن", "Yemen"],
    "somalia": ["SO", "Somalia"],
}


class RegionBlockerDB:
    def __init__(self):
        self.col: AsyncMotorCollection = db.region_blocker

    async def add_blocked_country(self, chat_id: int, countries: list):
        """Add blocked countries to chat"""
        countries_lower = [c.lower().strip() for c in countries]
        await self.col.update_one(
            {"_id": chat_id},
            {
                "$addToSet": {
                    "blocked_countries": {"$each": countries_lower}
                }
            },
            upsert=True,
        )

    async def add_blocked_lang(self, chat_id: int, languages: list):
        """Add blocked language scripts to chat"""
        languages_lower = [l.lower().strip() for l in languages]
        await self.col.update_one(
            {"_id": chat_id},
            {
                "$addToSet": {
                    "blocked_languages": {"$each": languages_lower}
                }
            },
            upsert=True,
        )

    async def remove_blocked_country(self, chat_id: int, countries: list):
        """Remove blocked countries from chat"""
        countries_lower = [c.lower().strip() for c in countries]
        await self.col.update_one(
            {"_id": chat_id},
            {
                "$pullAll": {
                    "blocked_countries": countries_lower
                }
            },
        )

    async def remove_blocked_lang(self, chat_id: int, languages: list):
        """Remove blocked languages from chat"""
        languages_lower = [l.lower().strip() for l in languages]
        await self.col.update_one(
            {"_id": chat_id},
            {
                "$pullAll": {
                    "blocked_languages": languages_lower
                }
            },
        )

    async def get_chat_blocks(self, chat_id: int):
        """Get blocked countries and languages for chat"""
        data = await self.col.find_one({"_id": chat_id})
        return {
            "countries": data.get("blocked_countries", []) if data else [],
            "languages": data.get("blocked_languages", []) if data else []
        }

    async def clear_blocks(self, chat_id: int):
        """Clear all blocks for chat"""
        await self.col.delete_one({"_id": chat_id})


blocker_db = RegionBlockerDB()


async def is_admin_or_sudo(client: Client, user_id: int, chat_id: int) -> bool:
    """Check if user is admin or sudoer"""
    if user_id in SUDOERS:
        return True
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.privileges and member.privileges.can_delete_messages
    except:
        return False


def detect_language_script(text: str) -> list:
    """Detect language scripts in text"""
    detected = []
    if not text:
        return detected
    
    for lang_name, lang_data in LANGUAGE_SCRIPTS.items():
        if re.search(lang_data["pattern"], text):
            detected.append(lang_name)
    
    return detected


def is_likely_from_country(user: ChatMember, country: str) -> bool:
    """
    Check if user might be from a specific country based on:
    - First name/Last name patterns
    - Username patterns
    """
    country = country.lower().strip()
    
    if country not in COUNTRY_CODES:
        return False
    
    codes = COUNTRY_CODES[country]
    
    # Build searchable text from user data
    search_text = ""
    if user.user.first_name:
        search_text += user.user.first_name.lower()
    if user.user.last_name:
        search_text += " " + user.user.last_name.lower()
    if user.user.username:
        search_text += " " + user.user.username.lower()
    
    # Check for language scripts in names
    scripts = detect_language_script(search_text)
    
    # Country-to-script mapping
    country_scripts = {
        "india": ["hindi"],
        "china": ["chinese"],
        "russia": ["cyrillic"],
        "ukraine": ["cyrillic"],
        "belarus": ["cyrillic"],
        "iran": ["persian", "arabic"],
        "iraq": ["arabic"],
        "egypt": ["arabic"],
        "saudi_arabia": ["arabic"],
        "uae": ["arabic"],
        "lebanon": ["arabic"],
        "yemen": ["arabic"],
        "syria": ["arabic"],
        "thailand": ["thai"],
        "korea": ["korean"],
        "south_korea": ["korean"],
        "georgia": ["georgian"],
        "mongolia": ["mongolian"],
    }
    
    expected_scripts = country_scripts.get(country, [])
    if expected_scripts and any(s in scripts for s in expected_scripts):
        return True
    
    # Check country codes in text
    for code in codes:
        if code.lower() in search_text:
            return True
    
    return False


@app.on_message(filters.command("block"))
async def block_countries(client: Client, message: Message):
    """Block specific countries"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can use this command!")
        return

    if len(message.command) < 2:
        countries_list = ", ".join(COUNTRY_CODES.keys())
        await message.reply_text(
            f"❌ Please specify countries to block!\n\n"
            f"Usage: `/block india,china,russia` \n\n"
            f"Available: {countries_list}"
        )
        return

    countries = message.command[1].split(",")
    valid_countries = []
    invalid_countries = []

    for country in countries:
        country = country.lower().strip()
        if country in COUNTRY_CODES:
            valid_countries.append(country)
        else:
            invalid_countries.append(country)

    if valid_countries:
        await blocker_db.add_blocked_country(message.chat.id, valid_countries)
        text = f"✅ Blocked: {', '.join(valid_countries)}\n"
    else:
        text = ""

    if invalid_countries:
        text += f"❌ Unknown countries: {', '.join(invalid_countries)}"

    await message.reply_text(text)


@app.on_message(filters.command("blocklang"))
async def block_languages(client: Client, message: Message):
    """Block specific language scripts"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can use this command!")
        return

    if len(message.command) < 2:
        langs_list = ", ".join(LANGUAGE_SCRIPTS.keys())
        await message.reply_text(
            f"❌ Please specify languages to block!\n\n"
            f"Usage: `/blocklang cyrillic,arabic,chinese` \n\n"
            f"Available: {langs_list}"
        )
        return

    languages = message.command[1].split(",")
    valid_langs = []
    invalid_langs = []

    for lang in languages:
        lang = lang.lower().strip()
        if lang in LANGUAGE_SCRIPTS:
            valid_langs.append(lang)
        else:
            invalid_langs.append(lang)

    if valid_langs:
        await blocker_db.add_blocked_lang(message.chat.id, valid_langs)
        text = f"✅ Blocked: {', '.join(valid_langs)}\n"
    else:
        text = ""

    if invalid_langs:
        text += f"❌ Unknown languages: {', '.join(invalid_langs)}"

    await message.reply_text(text)


@app.on_message(filters.command("unblock"))
async def unblock_countries(client: Client, message: Message):
    """Unblock specific countries"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can use this command!")
        return

    if len(message.command) < 2:
        await message.reply_text(
            "❌ Please specify countries to unblock!\n\n"
            "Usage: `/unblock russia,india` "
        )
        return

    countries = message.command[1].split(",")
    await blocker_db.remove_blocked_country(message.chat.id, countries)
    await message.reply_text(f"✅ Unblocked: {', '.join(countries)}")


@app.on_message(filters.command("unblocklang"))
async def unblock_languages(client: Client, message: Message):
    """Unblock specific languages"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can use this command!")
        return

    if len(message.command) < 2:
        await message.reply_text(
            "❌ Please specify languages to unblock!\n\n"
            "Usage: `/unblocklang cyrillic,arabic` "
        )
        return

    languages = message.command[1].split(",")
    await blocker_db.remove_blocked_lang(message.chat.id, languages)
    await message.reply_text(f"✅ Unblocked: {', '.join(languages)}")


@app.on_message(filters.command("blocklist"))
async def show_blocklist(client: Client, message: Message):
    """Show blocked countries and languages"""
    
    blocks = await blocker_db.get_chat_blocks(message.chat.id)
    
    text = "🛡️ **Block List for this Chat:**\n\n"
    
    if blocks["countries"]:
        text += f"🚫 **Blocked Countries:** {', '.join(blocks['countries'])}\n\n"
    else:
        text += "🚫 **Blocked Countries:** None\n\n"
    
    if blocks["languages"]:
        text += f"📝 **Blocked Language Scripts:** {', '.join(blocks['languages'])}\n"
    else:
        text += "📝 **Blocked Language Scripts:** None\n"
    
    await message.reply_text(text)


@app.on_message(filters.command("clearblocklist"))
async def clear_blocklist(client: Client, message: Message):
    """Clear all blocks for chat"""
    
    is_admin = await is_admin_or_sudo(client, message.from_user.id, message.chat.id)
    if not is_admin:
        await message.reply_text("❌ Only admins and sudoers can use this command!")
        return

    await blocker_db.clear_blocks(message.chat.id)
    await message.reply_text("✅ All blocks cleared for this chat!")


@app.on_chat_member_updated()
async def check_new_member(client: Client, update):
    """Check new members against blocklist"""
    
    # Only check new members
    if update.new_chat_member.status == "member" and \
       (not hasattr(update.old_chat_member, 'status') or 
        update.old_chat_member.status not in ["member", "restricted"]):
        
        chat_id = update.chat.id
        user = update.new_chat_member.user
        
        # Get blocklist for this chat
        blocks = await blocker_db.get_chat_blocks(chat_id)
        
        # Check language scripts in username/names
        if blocks["languages"]:
            search_text = ""
            if user.first_name:
                search_text += user.first_name
            if user.last_name:
                search_text += " " + user.last_name
            if user.username:
                search_text += " " + user.username
            
            detected_scripts = detect_language_script(search_text)
            
            for blocked_lang in blocks["languages"]:
                if blocked_lang in detected_scripts:
                    try:
                        await client.ban_chat_member(chat_id, user.id)
                        logger.info(
                            f"Kicked {user.id} from {chat_id} - "
                            f"Blocked language script: {blocked_lang}"
                        )
                        await client.send_message(
                            chat_id,
                            f"🛡️ Removed user with blocked language script ({blocked_lang})"
                        )
                    except Exception as e:
                        logger.error(f"Error kicking user: {e}")
                    return
        
        # Check country indicators
        if blocks["countries"]:
            member = await client.get_chat_member(chat_id, user.id)
            
            for blocked_country in blocks["countries"]:
                if is_likely_from_country(member, blocked_country):
                    try:
                        await client.ban_chat_member(chat_id, user.id)
                        logger.info(
                            f"Kicked {user.id} from {chat_id} - "
                            f"Blocked country: {blocked_country}"
                        )
                        await client.send_message(
                            chat_id,
                            f"🛡️ Removed user from blocked region ({blocked_country})"
                        )
                    except Exception as e:
                        logger.error(f"Error kicking user: {e}")
                    return
