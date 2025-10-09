"""
Music Module - Download and search for music
Supports YouTube, SoundCloud, and other platforms via ARQ
"""

import asyncio
import datetime
import logging
import os
from functools import partial
from io import BytesIO

from pyrogram import filters
from pytube import YouTube
from requests import get

from wbb import aiohttpsession as session
from wbb import app, arq, SUDOERS
from wbb.core.decorators.errors import capture_err
from wbb.utils.pastebin import paste

logger = logging.getLogger(__name__)

__MODULE__ = "Music"
__HELP__ = """
**Music Module**

Download and search for music from various sources.

**Commands:**

`/ytmusic [link or query]`  - Download music from YouTube or search [SUDOERS]
`/saavn [query]`  - Download music from Saavn (JioSaavn)
`/lyrics [query]`  - Get lyrics for a song

**Examples:**

`/ytmusic https://youtube.com/watch?v=...`
`/ytmusic Bohemian Rhapsody` 
`/saavn Shape of You` 
`/lyrics Blinding Lights` 

**Note:** Video duration limit is 30 minutes for YouTube downloads
"""

# Use asyncio lock instead of global flag for better concurrency control
download_lock = asyncio.Lock()
MAX_DURATION = 1800  # 30 minutes in seconds
TEMP_DIR = "downloads"

# Ensure temp directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


def download_youtube_audio(arq_resp):
    """Download audio from YouTube response"""
    try:
        r = arq_resp.result[0]
        title = r.title
        performer = r.channel
        
        # Parse duration safely
        m, s = r.duration.split(":")
        duration = int(datetime.timedelta(minutes=int(m), seconds=int(s)).total_seconds())
        
        # Check duration limit
        if duration > MAX_DURATION:
            return None
        
        # Download thumbnail
        try:
            thumb = get(r.thumbnails[0], timeout=5).content
            thumbnail_file = os.path.join(TEMP_DIR, f"thumbnail_{title[:50]}.png")
            with open(thumbnail_file, "wb") as f:
                f.write(thumb)
        except Exception as e:
            logger.warning(f"Failed to download thumbnail: {e}")
            thumbnail_file = None
        
        # Download from YouTube
        url = f"https://youtube.com{r.url_suffix}"
        yt = YouTube(url)
        audio = yt.streams.filter(only_audio=True).first()
        
        if not audio:
            return None
        
        out_file = audio.download(output_path=TEMP_DIR)
        base, _ = os.path.splitext(out_file)
        audio_file = base + ".mp3"
        
        try:
            os.rename(out_file, audio_file)
        except FileExistsError:
            os.remove(out_file)
        
        return {
            "title": title,
            "performer": performer,
            "duration": duration,
            "audio_file": audio_file,
            "thumbnail_file": thumbnail_file
        }
    
    except Exception as e:
        logger.error(f"Error downloading YouTube audio: {e}")
        return None


@app.on_message(filters.command("ytmusic"))
@capture_err
async def music(_, message):
    """Download music from YouTube"""
    
    # Check if user is sudoer
    if message.from_user.id not in SUDOERS:
        return await message.reply_text(
            "❌ This command is only available for sudoers!"
        )
    
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage: `/ytmusic [YouTube URL or search query]` "
        )
    
    query = message.text.split(None, 1)[1]
    
    # Use lock to prevent multiple concurrent downloads
    if download_lock.locked():
        return await message.reply_text(
            "⏳ Another download is in progress. Please wait..."
        )
    
    async with download_lock:
        status_msg = await message.reply_text(
            f"🎵 Searching for: `{query}` ..."
        )
        
        try:
            # Search for the song
            arq_resp = await arq.youtube(query)
            
            if not arq_resp or not arq_resp.result:
                return await status_msg.edit_text(
                    "❌ No results found for your query."
                )
            
            await status_msg.edit_text(
                f"⬇️ Downloading: `{arq_resp.result[0].title}` ..."
            )
            
            # Download in executor to avoid blocking
            loop = asyncio.get_event_loop()
            music_data = await loop.run_in_executor(
                None, partial(download_youtube_audio, arq_resp)
            )
            
            if not music_data:
                return await status_msg.edit_text(
                    "❌ **Error:** Video is too long (max 30 minutes allowed)"
                )
            
            # Send the audio file
            await message.reply_audio(
                audio=music_data["audio_file"],
                duration=music_data["duration"],
                performer=music_data["performer"],
                title=music_data["title"],
                thumb=music_data["thumbnail_file"] if music_data["thumbnail_file"] else None,
            )
            
            await status_msg.delete()
            
            # Cleanup files
            try:
                if os.path.exists(music_data["audio_file"]):
                    os.remove(music_data["audio_file"])
                if music_data["thumbnail_file"] and os.path.exists(music_data["thumbnail_file"]):
                    os.remove(music_data["thumbnail_file"])
            except Exception as e:
                logger.warning(f"Failed to cleanup files: {e}")
        
        except Exception as e:
            logger.error(f"Error in music download: {e}")
            await status_msg.edit_text(
                f"❌ **Error:** {str(e)[:100]}"
            )


async def download_song(url):
    """Download song from URL"""
    try:
        async with session.get(url, timeout=30) as resp:
            song = await resp.read()
        song_bytes = BytesIO(song)
        song_bytes.name = "song.mp3"
        return song_bytes
    except Exception as e:
        logger.error(f"Error downloading song: {e}")
        return None


@app.on_message(filters.command("saavn"))
@capture_err
async def saavn_music(_, message):
    """Download music from Saavn (JioSaavn)"""
    
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage: `/saavn [song name]` "
        )
    
    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔍 Searching on Saavn...")
    
    try:
        resp = await arq.saavn(query)
        
        if not resp or not resp.result:
            return await m.edit("❌ No results found on Saavn.")
        
        song = resp.result[0]
        song_name = song.get("song", "Unknown")
        artist = song.get("artist", "Unknown")
        url = song.get("url")
        
        if not url:
            return await m.edit("❌ Could not fetch song URL.")
        
        await m.edit(f"⬇️ Downloading: `{song_name}` ...")
        
        song_file = await download_song(url)
        
        if not song_file:
            return await m.edit("❌ Failed to download the song.")
        
        await message.reply_audio(
            audio=song_file,
            title=song_name,
            performer=artist
        )
        
        await m.delete()
    
    except Exception as e:
        logger.error(f"Error in Saavn: {e}")
        await m.edit(f"❌ **Error:** {str(e)[:100]}")


@app.on_message(filters.command("lyrics"))
@capture_err
async def lyrics_func(_, message):
    """Get lyrics for a song"""
    
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage: `/lyrics [song name]` "
        )
    
    query = message.text.strip().split(None, 1)[1]
    m = await message.reply_text("🔍 Searching for lyrics...")
    
    try:
        resp = await arq.lyrics(query)
        
        if not resp or not resp.ok or not resp.result:
            return await m.edit("❌ No lyrics found for that song.")
        
        song = resp.result[0]
        song_name = song.get("song", "Unknown")
        artist = song.get("artist", "Unknown")
        lyrics = song.get("lyrics", "N/A")
        
        # Format message
        msg = f"🎵 **{song_name}** | **{artist}**\n\n{lyrics}"
        
        # If too long, use pastebin
        if len(msg) > 4095:
            try:
                paste_url = await paste(msg)
                msg = f"🎵 **{song_name}** | **{artist}**\n\n[Lyrics too long - Click here]({paste_url})"
            except Exception as e:
                logger.error(f"Pastebin error: {e}")
                msg = f"🎵 **{song_name}** | **{artist}**\n\n⚠️ Lyrics too long to display"
        
        await m.edit(msg)
    
    except Exception as e:
        logger.error(f"Error fetching lyrics: {e}")
        await m.edit(f"❌ **Error:** {str(e)[:100]}")
