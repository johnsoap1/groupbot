<h1 align="center"> 
    ✨ WilliamButcherBot ✨ 
</h1>

<h3 align="center"> 
    Telegram Group Manager Bot + Userbot Written In Python Using Pyrogram.
</h3>

<p align="center">
    <a href="https://python.org">
        <img src="http://forthebadge.com/images/badges/made-with-python.svg" alt="made-with-python">
    </a>
    <a href="https://GitHub.com/TheHamkerCat">
        <img src="http://ForTheBadge.com/images/badges/built-with-love.svg" alt="built-with-love">
    </a> <br>
    <img src="https://img.shields.io/github/license/thehamkercat/WilliamButcherBot?style=for-the-badge&logo=appveyor" alt="LICENSE">
    <img src="https://img.shields.io/github/contributors/thehamkercat/WilliamButcherBot?style=for-the-badge&logo=appveyor" alt="Contributors">
    <img src="https://img.shields.io/github/repo-size/thehamkercat/WilliamButcherBot?style=for-the-badge&logo=appveyor" alt="Repository Size"> <br>
    <img src="https://img.shields.io/badge/python-3.9-green?style=for-the-badge&logo=appveyor" alt="Python Version">
    <img src="https://img.shields.io/github/issues/thehamkercat/WilliamButcherBot?style=for-the-badge&logo=appveyor" alt="Issues">
    <img src="https://img.shields.io/github/forks/thehamkercat/WilliamButcherBot?style=for-the-badge&logo=appveyor" alt="Forks">
    <img src="https://img.shields.io/github/stars/thehamkercat/WilliamButcherBot?style=for-the-badge&logo=appveyor" alt="Stars">
</p>

<h3 align="center"> 
    Ready to use method
</h3>

<p align="center">
    A Support Group and ready-to-use running instance of this bot can be found on Telegram <br>
    <a href="https://t.me/WilliamButcherBot"> WilliamButcherBot </a> | 
    <a href="https://t.me/wbbsupport"> WbbSupport </a>
</p>

<h2 align="center"> 
   ⇝ Requirements ⇜
</h2>

<p align="center">
    <a href="https://www.python.org/downloads/release/python-390/"> Python3.9 </a> |
    <a href="https://docs.pyrogram.org/intro/setup#api-keys"> Telegram API Key </a> |
    <a href="https://t.me/botfather"> Telegram Bot Token </a> | 
    <a href="https://telegra.ph/How-To-get-Mongodb-URI-04-06"> MongoDB URI </a>
</p>

<h2 align="center"> 
   ⇝ Install Locally Or On A VPS ⇜
</h2>

```console
thehamkercat@arch:~$ git clone https://github.com/thehamkercat/WilliamButcherBot
thehamkercat@arch:~$ cd WilliamButcherBot
thehamkercat@arch:~$ pip3 install -U -r requirements.txt
thehamkercat@arch:~$ cp sample_config.py config.py
```
 
<h3 align="center"> 
    Edit <b>config.py</b> with your own values
</h3>

<h2 align="center"> 
   ⇝ Run Directly ⇜
</h2>

```console
thehamkercat@arch:~$ python3 -m wbb
```

<h3 align="center"> 
   Generating Pyrogram Session For Heroku
</h3>

```console
thehamkercat@arch:~$ git clone https://github.com/thehamkercat/WilliamButcherBot
thehamkercat@arch:~$ cd WilliamButcherBot
thehamkercat@arch:~$ pip3 install pyrogram TgCrypto
thehamkercat@arch:~$ python3 str_gen.py
```

<h1 align="center"> 
   ⇝ Docker ⇜
</h1>

```console
thehamkercat@arch:~$ git clone https://github.com/thehamkercat/WilliamButcherBot
thehamkercat@arch:~$ cd WilliamButcherBot
thehamkercat@arch:~$ cp sample_config.env config.env
```

<h3 align="center"> 
    Edit <b> config.env </b> with your own values
</h3>

```console
thehamkercat@arch:~$ sudo docker build . -t wbb
thehamkercat@arch:~$ sudo docker run wbb
```

<h2 align="center">
   ⇝ Available Modules ⇜
</h2>

### 🤖 Administration
- `admin.py` - Core admin commands (ban, mute, promote, etc.)
- `admin_misc.py` - Additional admin utilities
- `sudoers.py` - Sudo user management
- `flood.py` - Anti-flood protection
- `locks.py` - Chat permission locks
- `blacklist.py` - User blacklisting
- `blacklist_chat.py` - Chat blacklisting
- `region_blocker.py` - Regional restrictions

### 👋 Greetings & Welcome
- `greetings.py` - Welcome messages and captcha
- `autoapprove.py` - Auto-approve join requests
- `pmpermit.py` - PM security and permissions

### 🔍 Information & Utilities
- `info.py` - User and chat information
- `global_stats.py` - Bot usage statistics
- `command_cleaner.py` - Clean up command messages
- `misc.py` - Miscellaneous utility commands
- `dice.py` - Dice and random number generation
- `carbon.py` - Code to image generation
- `quotly.py` - Create quote messages
- `telegraph.py` - Upload files to Telegraph
- `translate.py` - Message translation
- `tts.py` - Text-to-speech conversion

### 🛡️ Security & Moderation
- `antiservice.py` - Service message handling
- `chat_watcher.py` - Monitor chat activities
- `feds.py` - Federation ban system
- `filters.py` - Custom chat filters
- `regex.py` - Regex pattern matching
- `taglogger.py` - Log user mentions
- `trigger.py` - Custom triggers and responses

### 🎵 Media & Files
- `download_upload.py` - File handling
- `music.py` - Music playback
- `stickers.py` - Sticker utilities
- `parse_preview.py` - Link previews

### 🛠️ System & Maintenance
- `arq.py` - ARQ task queue
- `mongo_backup.py` - Database backups
- `sudo.py` - Sudo commands
- `userbot.py` - Userbot functionality

### 🔄 Automation
- `autocorrect.py` - Auto-correct messages
- `pipes.py` - Message piping between chats
- `rss.py` - RSS feed monitoring

### 🎮 Fun & Games
- `couple.py` - Couple pairing
- `create.py` - Create custom commands
- `reverse.py` - Reverse image search

<h2 align="center">
   ⇝ Write New Modules ⇜
</h2>

```py
# Add license text here, get it from below

from wbb import app # This is bot's client
from wbb import app2 # userbot client, import it if module is related to userbot
from pyrogram import filters # pyrogram filters
...


# For /help menu
__MODULE__ = "Module Name"
__HELP__ = "Module help message"


@app.on_message(filters.command("start"))
async def some_function(_, message):
    await message.reply_text("I'm already up!!")

# Many useful functions are in, wbb/utils/, wbb, and wbb/core/
```

<h3 align="center"> 
   And put that file in wbb/modules/, restart and test your bot.
</h3>

<b>Discover more awesome plugin add-ons for this repo</b> [@WilliamButcherBot-Add-ons](https://github.com/si-nn-er-ls/WilliamButcherBot-Add-ons).
