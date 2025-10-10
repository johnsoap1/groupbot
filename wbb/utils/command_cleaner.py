"""
Command Message Cleaner Module

This module provides a decorator to automatically delete command messages after they're processed.
"""
from functools import wraps
from contextlib import suppress
from typing import Callable, Any, Awaitable, TypeVar, Union

from pyrogram.types import Message, CallbackQuery

T = TypeVar('T')

async def _delete_message(message: Union[Message, CallbackQuery]) -> None:
    """Safely delete a message or callback query."""
    with suppress(Exception):
        if isinstance(message, CallbackQuery):
            await message.message.delete()
        else:
            await message.delete()

def delete_command_message(func: T) -> T:
    """
    Decorator that automatically deletes the command message after the handler completes.
    
    Usage:
        @app.on_message(filters.command("example"))
        @delete_command_message
        async def example_handler(_, message: Message):
            await message.reply("Command processed!")
    """
    @wraps(func)
    async def wrapper(client: Any, message: Union[Message, CallbackQuery]) -> Any:
        try:
            # Execute the original function
            result = await func(client, message)
            # Delete the command message after successful execution
            await _delete_message(message)
            return result
        except Exception as e:
            # Still try to delete the message even if command fails
            await _delete_message(message)
            raise e
    
    return wrapper

def delete_command_message_async(func: T) -> T:
    """
    Alternative version that deletes the message immediately before command execution.
    
    This is useful for commands that might take a while to process.
    """
    @wraps(func)
    async def wrapper(client: Any, message: Union[Message, CallbackQuery]) -> Any:
        # Delete the command message before processing
        await _delete_message(message)
        # Execute the original function
        return await func(client, message)
    
    return wrapper
