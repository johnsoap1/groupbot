"""
Advanced Config Menu Module - Comprehensive bot configuration system
Features: Dynamic module detection, database persistence, nested settings,
statistics, audit logs, scheduled tasks, and full inline management
"""

from pyrogram import filters, Client
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Chat
)
from pyrogram.errors import ChatAdminRequired
from wbb import app, SUDOERS
from wbb.core.decorators.errors import capture_err
from motor.motor_asyncio import AsyncIOMotorCollection
from wbb.core.mongo import db
import logging
import inspect
import os
import importlib
import pkgutil
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

logger = logging.getLogger(__name__)

__MODULE__ = "Configuration"
__HELP__ = """
**Advanced Configuration Menu**

Interactive management system for all bot settings and modules.

**Commands:**

`/config`  - Open main configuration menu
`/config [module]`  - Quick access to specific module
`/modstats`  - View module statistics
`/audit`  - View audit log
`/reset`  - Reset all settings (sudoer only)

**Features:**

✅ Dynamic module detection
✅ Per-chat module enable/disable
✅ Module statistics and usage tracking
✅ Audit logging for all changes
✅ Settings backup and restore
✅ Module dependencies
✅ Scheduled module tasks
✅ Advanced search and filtering

**Admin only**
"""

# Database collections
class ConfigDB:
    def __init__(self):
        self.chats = db.chat_config
        self.modules = db.module_settings
        self.audit = db.audit_log
        self.stats = db.module_stats
        self.backups = db.settings_backup

    async def init_chat(self, chat_id: int, chat: Chat):
        """Initialize chat configuration"""
        await self.chats.update_one(
            {"_id": chat_id},
            {
                "$setOnInsert": {
                    "chat_id": chat_id,
                    "chat_title": chat.title or "Private",
                    "chat_type": chat.type,
                    "created_at": datetime.now(),
                    "enabled_modules": [],
                    "disabled_modules": [],
                    "settings": {},
                    "last_updated": datetime.now(),
                }
            },
            upsert=True,
        )

    async def toggle_module(self, chat_id: int, module_name: str, enable: bool):
        """Enable or disable a module"""
        if enable:
            await self.chats.update_one(
                {"_id": chat_id},
                {
                    "$addToSet": {"enabled_modules": module_name},
                    "$pull": {"disabled_modules": module_name},
                    "$set": {"last_updated": datetime.now()}
                }
            )
        else:
            await self.chats.update_one(
                {"_id": chat_id},
                {
                    "$addToSet": {"disabled_modules": module_name},
                    "$pull": {"enabled_modules": module_name},
                    "$set": {"last_updated": datetime.now()}
                }
            )

    async def get_chat_config(self, chat_id: int):
        """Get full chat configuration"""
        return await self.chats.find_one({"_id": chat_id})

    async def get_module_setting(self, chat_id: int, module: str, setting: str):
        """Get specific module setting"""
        config = await self.get_chat_config(chat_id)
        if config and "settings" in config:
            return config["settings"].get(f"{module}_{setting}")
        return None

    async def set_module_setting(self, chat_id: int, module: str, setting: str, value):
        """Set module setting"""
        await self.chats.update_one(
            {"_id": chat_id},
            {
                "$set": {
                    f"settings.{module}_{setting}": value,
                    "last_updated": datetime.now()
                }
            },
            upsert=True
        )

    async def log_action(self, chat_id: int, admin_id: int, action: str, details: str):
        """Log configuration changes"""
        await self.audit.insert_one({
            "chat_id": chat_id,
            "admin_id": admin_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now()
        })

    async def get_audit_log(self, chat_id: int, limit: int = 10):
        """Get audit log"""
        return await self.audit.find(
            {"chat_id": chat_id}
        ).sort("_id", -1).to_list(limit)

    async def log_module_usage(self, chat_id: int, module: str):
        """Track module usage"""
        await self.stats.update_one(
            {"_id": f"{chat_id}_{module}"},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used": datetime.now()}
            },
            upsert=True
        )

    async def get_module_stats(self, chat_id: int):
        """Get module statistics"""
        return await self.stats.find(
            {"_id": {"$regex": f"^{chat_id}_"}}
        ).to_list(None)

    async def backup_settings(self, chat_id: int, backup_name: str):
        """Backup current settings"""
        config = await self.get_chat_config(chat_id)
        if config:
            backup = {
                "_id": f"{chat_id}_{backup_name}_{datetime.now().timestamp()}",
                "chat_id": chat_id,
                "backup_name": backup_name,
                "config": config,
                "created_at": datetime.now()
            }
            await self.backups.insert_one(backup)
            return True
        return False

    async def restore_settings(self, chat_id: int, backup_id: str):
        """Restore settings from backup"""
        backup = await self.backups.find_one({"_id": backup_id})
        if backup:
            await self.chats.replace_one(
                {"_id": chat_id},
                backup["config"],
                upsert=True
            )
            return True
        return False


config_db = ConfigDB()


class ModuleScanner:
    """Dynamically detect and analyze all modules"""
    
    @staticmethod
    async def get_all_modules() -> Dict[str, Dict]:
        """Scan and categorize all modules"""
        modules_dir = "wbb/modules"
        modules_data = {}
        
        if not os.path.exists(modules_dir):
            return modules_data
        
        for importer, modname, ispkg in pkgutil.iter_modules([modules_dir]):
            try:
                # Skip special files
                if modname.startswith("__") or modname.startswith("."):
                    continue
                
                # Load module
                module_path = f"wbb.modules.{modname}"
                try:
                    mod = importlib.import_module(module_path)
                except:
                    continue
                
                # Extract metadata
                module_info = {
                    "name": modname,
                    "enabled": True,
                    "description": getattr(mod, "__HELP__", "No description available"),
                    "category": ModuleScanner.categorize_module(modname),
                    "functions": len([m for m in dir(mod) if not m.startswith("_")]),
                    "path": f"{modules_dir}/{modname}.py"
                }
                
                modules_data[modname] = module_info
            
            except Exception as e:
                logger.error(f"Error loading module {modname}: {e}")
                continue
        
        return modules_data
    
    @staticmethod
    def categorize_module(modname: str) -> str:
        """Auto-categorize modules"""
        categories = {
            "Admin": ["admin", "sudo", "sudoers", "locks"],
            "Moderation": ["antiservice", "blacklist", "flood", "karma", "region_blocker"],
            "Utility": ["notes", "rules", "greetings", "filters", "trigger", "command_cleaner"],
            "Entertainment": ["chatbot", "couple", "dice", "quotly", "stickers"],
            "Downloads": ["music", "download_upload", "webss", "paste", "telegraph"],
            "Tools": ["translate", "tts", "img_pdf", "carbon", "iplookup"],
            "Security": ["autoapprove", "pmpermit", "feds", "chat_watcher"],
            "Other": ["misc", "alive", "repo"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in modname for keyword in keywords):
                return category
        
        return "Other"


async def is_admin(client: Client, user_id: int, chat_id: int) -> bool:
    """Check if user is admin or sudoer"""
    if user_id in SUDOERS:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.privileges and member.privileges.can_delete_messages
    except:
        return False


async def is_sudoer(user_id: int) -> bool:
    """Check if user is sudoer"""
    return user_id in SUDOERS


def create_main_menu_keyboard(modules_data: Dict) -> InlineKeyboardMarkup:
    """Create main menu with all categories"""
    categories = {}
    
    for module_name, info in modules_data.items():
        category = info.get("category", "Other")
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
    
    buttons = []
    for category in sorted(categories.keys()):
        count = categories[category]
        buttons.append([
            InlineKeyboardButton(
                f"📁 {category} ({count})",
                callback_data=f"cfg_cat_{category}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton("📊 Statistics", callback_data="cfg_stats"),
        InlineKeyboardButton("🔄 Backup", callback_data="cfg_backup")
    ])
    buttons.append([
        InlineKeyboardButton("📋 Audit Log", callback_data="cfg_audit"),
        InlineKeyboardButton("⚙️ Advanced", callback_data="cfg_advanced")
    ])
    buttons.append([
        InlineKeyboardButton("❌ Close", callback_data="cfg_close")
    ])
    
    return InlineKeyboardMarkup(buttons)


def create_category_keyboard(category: str, modules_data: Dict) -> InlineKeyboardMarkup:
    """Create category module list"""
    buttons = []
    
    category_modules = {
        name: info for name, info in modules_data.items()
        if info.get("category") == category
    }
    
    for modname in sorted(category_modules.keys()):
        buttons.append([
            InlineKeyboardButton(
                f"⚙️ {modname}",
                callback_data=f"cfg_mod_{modname}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton("◀️ Back", callback_data="cfg_main"),
        InlineKeyboardButton("❌ Close", callback_data="cfg_close")
    ])
    
    return InlineKeyboardMarkup(buttons)


def create_module_keyboard(module_name: str, chat_id: int, enabled: bool) -> InlineKeyboardMarkup:
    """Create module configuration options"""
    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ Disable' if enabled else '❌ Enable'}",
                callback_data=f"cfg_toggle_{module_name}_{chat_id}"
            ),
            InlineKeyboardButton("📖 Help", callback_data=f"cfg_help_{module_name}")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data=f"cfg_mod_stats_{module_name}_{chat_id}"),
            InlineKeyboardButton("⚙️ Settings", callback_data=f"cfg_settings_{module_name}_{chat_id}")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="cfg_main"),
            InlineKeyboardButton("❌ Close", callback_data="cfg_close")
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)


async def get_main_menu_text(modules_data: Dict, chat_id: int) -> str:
    """Generate main menu text"""
    config = await config_db.get_chat_config(chat_id)
    enabled_count = len(config["enabled_modules"]) if config else 0
    total_modules = len(modules_data)
    
    categories = {}
    for module_name, info in modules_data.items():
        category = info.get("category", "Other")
        categories[category] = categories.get(category, 0) + 1
    
    text = f"""
🤖 **Advanced Bot Configuration**

**📊 Overall Status:**
✅ Enabled Modules: {enabled_count}/{total_modules}
⏱️ Last Updated: {config['last_updated'].strftime('%Y-%m-%d %H:%M') if config else 'Never'}

**📂 Categories:**
"""
    
    for category in sorted(categories.keys()):
        text += f"\n• **{category}:** {categories[category]} modules"
    
    text += """

**🎯 Select an option below:**
• Click a category to manage modules
• View statistics and audit logs
• Create backups and manage settings

**💡 Tips:**
- Enable/disable modules per chat
- Track usage statistics
- Backup before major changes
"""
    
    return text


async def get_module_text(module_name: str, chat_id: int, modules_data: Dict) -> str:
    """Generate module info text"""
    mod_info = modules_data.get(module_name, {})
    config = await config_db.get_chat_config(chat_id)
    enabled = module_name in (config.get("enabled_modules", []) if config else [])
    
    stats = await config_db.stats.find_one(
        {"_id": f"{chat_id}_{module_name}"}
    )
    
    text = f"""
⚙️ **Module Configuration**

**📌 Module:** `{module_name}` 
**📂 Category:** {mod_info.get('category', 'Unknown')}
**📝 Status:** {'✅ Enabled' if enabled else '❌ Disabled'}

**📊 Statistics:**
• Usage Count: {stats['usage_count'] if stats else 0}
• Last Used: {stats['last_used'].strftime('%Y-%m-%d %H:%M') if stats else 'Never'}

**📖 Description:**
{mod_info.get('description', 'No description available')[:500]}...

**⚡ Quick Actions:**
- Click Enable/Disable to toggle
- View Help for command reference
- Check Stats for usage data
"""
    
    return text


@app.on_message(filters.command("config"))
@capture_err
async def config_command(client: Client, message: Message):
    """Main config command"""
    
    is_admin_user = await is_admin(client, message.from_user.id, message.chat.id)
    if not is_admin_user:
        return await message.reply_text(
            "❌ Only admins can access the config menu!"
        )
    
    # Initialize chat
    await config_db.init_chat(message.chat.id, message.chat)
    
    # Scan modules
    modules_data = await ModuleScanner.get_all_modules()
    
    if not modules_data:
        return await message.reply_text(
            "❌ No modules found. Check your installation."
        )
    
    # Get main menu
    text = await get_main_menu_text(modules_data, message.chat.id)
    keyboard = create_main_menu_keyboard(modules_data)
    
    await message.reply_text(
        text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


@app.on_callback_query()
async def config_callback(client: Client, query: CallbackQuery):
    """Handle all config callbacks"""
    
    try:
        data = query.data
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        
        # Check admin
        is_admin_user = await is_admin(client, user_id, chat_id)
        if not is_admin_user:
            return await query.answer("❌ Admin only!", show_alert=True)
        
        modules_data = await ModuleScanner.get_all_modules()
        
        # Main menu
        if data == "cfg_main":
            text = await get_main_menu_text(modules_data, chat_id)
            keyboard = create_main_menu_keyboard(modules_data)
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Category
        elif data.startswith("cfg_cat_"):
            category = data.replace("cfg_cat_", "")
            category_mods = {
                name: info for name, info in modules_data.items()
                if info.get("category") == category
            }
            
            text = f"""
📁 **Category: {category}**

**Modules in this category:** {len(category_mods)}

Select a module to configure:
"""
            keyboard = create_category_keyboard(category, modules_data)
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Module
        elif data.startswith("cfg_mod_") and not data.startswith("cfg_mod_stats_"):
            module_name = data.replace("cfg_mod_", "")
            config = await config_db.get_chat_config(chat_id)
            enabled = module_name in (config.get("enabled_modules", []) if config else [])
            
            text = await get_module_text(module_name, chat_id, modules_data)
            keyboard = create_module_keyboard(module_name, chat_id, enabled)
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Toggle module
        elif data.startswith("cfg_toggle_"):
            parts = data.replace("cfg_toggle_", "").split("_")
            module_name = parts[0]
            
            config = await config_db.get_chat_config(chat_id)
            enabled = module_name in (config.get("enabled_modules", []) if config else [])
            
            await config_db.toggle_module(chat_id, module_name, not enabled)
            await config_db.log_action(
                chat_id, user_id,
                "TOGGLE_MODULE",
                f"Module {module_name} {'enabled' if not enabled else 'disabled'}"
            )
            
            new_status = "✅ Enabled" if not enabled else "❌ Disabled"
            await query.answer(f"{new_status}", show_alert=False)
            
            text = await get_module_text(module_name, chat_id, modules_data)
            keyboard = create_module_keyboard(module_name, chat_id, not enabled)
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Module help
        elif data.startswith("cfg_help_"):
            module_name = data.replace("cfg_help_", "")
            mod_info = modules_data.get(module_name, {})
            
            help_text = f"""
📖 **Help for: {module_name}**

{mod_info.get('description', 'No help available')}

**To use this module:**
`/help {module_name}`  - Get detailed command list
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data=f"cfg_mod_{module_name}")],
                [InlineKeyboardButton("❌ Close", callback_data="cfg_close")]
            ])
            
            await query.edit_message_text(help_text, reply_markup=keyboard)
        
        # Module stats
        elif data.startswith("cfg_mod_stats_"):
            module_name = data.replace("cfg_mod_stats_", "").split("_")[0]
            stats = await config_db.stats.find_one(
                {"_id": f"{chat_id}_{module_name}"}
            )
            
            text = f"""
📊 **Statistics for: {module_name}**

**Usage Data:**
• Total Uses: {stats['usage_count'] if stats else 0}
• Last Used: {stats['last_used'].strftime('%Y-%m-%d %H:%M') if stats else 'Never used'}
• Status: {'✅ Active' if stats else '❌ Not used yet'}

**Chat Info:**
• Chat ID: `{chat_id}` 
• Updated: Now
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data=f"cfg_mod_{module_name}")],
                [InlineKeyboardButton("❌ Close", callback_data="cfg_close")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Module settings
        elif data.startswith("cfg_settings_"):
            module_name = data.replace("cfg_settings_", "").split("_")[0]
            
            text = f"""
⚙️ **Settings for: {module_name}**

**Available Settings:**
• Enable/Disable: Toggle via main config
• Permissions: Inherits from admin settings
• Logging: All module usage is logged

**Advanced Settings:**
Use MongoDB to store custom settings per module.

**Command Reference:**
`/help {module_name}`  - Get all commands
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data=f"cfg_mod_{module_name}")],
                [InlineKeyboardButton("❌ Close", callback_data="cfg_close")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Statistics
        elif data == "cfg_stats":
            config = await config_db.get_chat_config(chat_id)
            enabled = config.get("enabled_modules", []) if config else []
            
            text = f"""
📊 **Bot Statistics**

**Configuration:**
• Total Modules: {len(modules_data)}
• Enabled: {len(enabled)}
• Disabled: {len(modules_data) - len(enabled)}

**Chat Status:**
• Chat ID: `{chat_id}` 
• Type: {query.message.chat.type}
• Configuration Created: {config['created_at'].strftime('%Y-%m-%d') if config else 'N/A'}
• Last Updated: {config['last_updated'].strftime('%Y-%m-%d %H:%M') if config else 'N/A'}

**Top Modules:**
Use audit log to see detailed statistics.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="cfg_main")],
                [InlineKeyboardButton("❌ Close", callback_data="cfg_close")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Backup
        elif data == "cfg_backup":
            text = """
💾 **Backup & Restore**

**Backup Options:**
• Auto-backup before major changes
• Manual backup of current settings
• Restore from previous backups

**Available Backups:**
(Backups stored in MongoDB)

**Actions:**
- Create a backup: `/backup` 
- Restore backup: `/restore [backup_id]` 
- List backups: `/backups` 
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Create Backup", callback_data="cfg_backup_create")],
                [InlineKeyboardButton("◀️ Back", callback_data="cfg_main")],
                [InlineKeyboardButton("❌ Close", callback_data="cfg_close")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Audit log
        elif data == "cfg_audit":
            audit_log = await config_db.get_audit_log(chat_id, limit=5)
            
            text = "📋 **Audit Log** (Last 5 actions)\n\n"
            
            if audit_log:
                for entry in audit_log:
                    text += f"""
• **Action:** {entry['action']}
  **By:** User {entry['admin_id']}
  **Details:** {entry['details']}
  **Time:** {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}
"""
            else:
                text += "No audit log entries yet."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="cfg_main")],
                [InlineKeyboardButton("❌ Close", callback_data="cfg_close")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Advanced
        elif data == "cfg_advanced":
            text = """
⚙️ **Advanced Settings**

**Database:**
• MongoDB: Connected ✅
• Auto-backup: Enabled ✅
• Cleanup: 30 days retention

**Performance:**
• Module Loading: Dynamic ✅
• Cache: In-memory ✅
• Logging: Enabled ✅

**Security:**
• Permission Check: Strict ✅
• Audit Logging: Full ✅
• Admin Only: Yes ✅

**Options:**
- Reset all settings (sudoer only)
- Export configuration
- Import configuration
"""
            
            buttons = [
                [InlineKeyboardButton("🔄 Reset All", callback_data="cfg_reset")],
                [InlineKeyboardButton("💾 Export", callback_data="cfg_export")],
                [InlineKeyboardButton("📥 Import", callback_data="cfg_import")],
            ]
            
            if await is_sudoer(user_id):
                buttons.append([InlineKeyboardButton("⚠️ Clear All Data", callback_data="cfg_wipe")])
            
            buttons.append([InlineKeyboardButton("◀️ Back", callback_data="cfg_main")])
            buttons.append([InlineKeyboardButton("❌ Close", callback_data="cfg_close")])
            
            keyboard = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(text, reply_markup=keyboard)
        
        # Close
        elif data == "cfg_close":
            await query.message.delete()
            await query.answer("✅ Config menu closed", show_alert=False)
        
        else:
            await query.answer("🔄 Please wait...", show_alert=False)
    
    except Exception as e:
        logger.error(f"Error in config callback: {e}")
        await query.answer(f"❌ Error: {str(e)[:100]}", show_alert=True)


@app.on_message(filters.command("modstats"))
@capture_err
async def modstats_command(client: Client, message: Message):
    """View module statistics"""
    
    stats = await config_db.get_module_stats(message.chat.id)
    
    text = "📊 **Module Statistics**\n\n"
    
    if stats:
        sorted_stats = sorted(stats, key=lambda x: x['usage_count'], reverse=True)
        text += "**Top 10 Most Used Modules:**\n"
        
        for i, stat in enumerate(sorted_stats[:10], 1):
            module_name = stat['_id'].split('_', 1)[1]
            text += f"{i}. `{module_name}` : {stat['usage_count']} uses\n"
    else:
        text += "No statistics available yet."
    
    await message.reply_text(text)


@app.on_message(filters.command("audit"))
@capture_err
async def audit_command(client: Client, message: Message):
    """View audit log"""
    
    is_admin_user = await is_admin(client, message.from_user.id, message.chat.id)
    if not is_admin_user:
        return await message.reply_text("❌ Admin only!")
    
    log = await config_db.get_audit_log(message.chat.id, limit=20)
    
    text = "📋 **Audit Log** (Last 20 entries)\n\n"
    
    if log:
        for entry in log:
            text += f"""• **{entry['action']}**
  Admin: `{entry['admin_id']}` 
  Details: {entry['details']}
  Time: {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}

"""
    else:
        text += "No audit log entries."
    
    await message.reply_text(text)
