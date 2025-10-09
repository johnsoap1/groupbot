"""
Utility functions for handling user permissions.
"""
from wbb import app

async def member_permissions(chat_id: int, user_id: int):
    """
    Get a list of permissions for a chat member.
    
    Args:
        chat_id: The chat ID
        user_id: The user ID to check permissions for
        
    Returns:
        List[str]: List of permission strings the user has
    """
    perms = []
    try:
        member = (await app.get_chat_member(chat_id, user_id)).privileges
        if not member:
            return []
            
        if member.can_post_messages:
            perms.append("can_post_messages")
        if member.can_edit_messages:
            perms.append("can_edit_messages")
        if member.can_delete_messages:
            perms.append("can_delete_messages")
        if member.can_restrict_members:
            perms.append("can_restrict_members")
        if member.can_promote_members:
            perms.append("can_promote_members")
        if member.can_change_info:
            perms.append("can_change_info")
        if member.can_invite_users:
            perms.append("can_invite_users")
        if member.can_pin_messages:
            perms.append("can_pin_messages")
        if member.can_manage_video_chats:
            perms.append("can_manage_video_chats")
    except Exception as e:
        print(f"Error getting member permissions: {e}")
    
    return perms
