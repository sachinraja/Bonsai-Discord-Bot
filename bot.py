import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
import pymongo

from utils.default import default_user, default_presence, user_col, guild_col
from utils.embeds import error_embed

# load environmental variables
load_dotenv()

TOKEN = os.environ["BONSAI_TOKEN"]

# logging
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# prefixes
prefixes = ["b!"]

async def get_prefix(bot, msg):
    guild = guild_col.find_one({"guild_id" : msg.guild.id})

    if guild == None:
        return commands.when_mentioned_or(*prefixes)(bot, msg)
    
    return commands.when_mentioned_or(*guild["prefixes"])(bot, msg)

bot = commands.AutoShardedBot(command_prefix=get_prefix)

bot.remove_command("help")

initial_extensions = ["cogs.tree", "cogs.shop", "cogs.inventory", "cogs.balance", "cogs.management", "cogs.events", "cogs.info"]

@bot.event
async def on_ready():
    # Attempt to load all initial cogs for bot
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
            print(f"Loaded extension {extension}.")

        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

    print(f"Logged in as {bot.user}\n{'-' * 20}\n{bot.user.id}")

    # watching x amount of servers
    await bot.change_presence(activity=default_presence(bot))

bot.run(TOKEN)
