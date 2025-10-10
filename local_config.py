"""
Local configuration for the bot.
This file should be imported in your main bot file before any modules are loaded.
"""

# List of modules to load (empty list means load all)
MOD_LOAD = [
    # Core modules
    "admin",
    "admin_misc",
    "greetings",
    "command_cleaner",
    # Add other modules you want to load
]

# List of modules to exclude from loading
MOD_NOLOAD = [
    # Modules to exclude
    "userbot",  # Example: exclude userbot module
]

# Apply these settings to the wbb module
import sys
import wbb

# Update the module with our settings
wbb.MOD_LOAD = MOD_LOAD
wbb.MOD_NOLOAD = MOD_NOLOAD

print(f"[CONFIG] Module loading configured: {len(MOD_LOAD)} to load, {len(MOD_NOLOAD)} to exclude")
