"""
URL utility functions for WilliamButcherBot.
"""
from typing import List, Tuple, Optional

def extract_urls(reply_markup) -> List[Tuple[str, str, str]]:
    """
    Extract URLs from a message's reply markup.
    
    Args:
        reply_markup: The reply markup object from a message
        
    Returns:
        List of tuples containing (button_name, button_text, button_url)
    """
    if not reply_markup or not hasattr(reply_markup, 'inline_keyboard'):
        return []
    
    urls = []
    for row in reply_markup.inline_keyboard:
        for button in row:
            if hasattr(button, 'url'):
                button_text = getattr(button, 'text', '')
                button_url = getattr(button, 'url', '')
                if button_url:
                    urls.append((button.text, button_text, button_url))
    
    return urls

def format_urls(urls: List[Tuple[str, str, str]]) -> str:
    """
    Format a list of URL tuples into a string.
    
    Args:
        urls: List of (name, text, url) tuples
        
    Returns:
        Formatted string of URLs
    """
    if not urls:
        return ""
    return "\n".join([f"{name}=[{text}, {url}]" for name, text, url in urls])
