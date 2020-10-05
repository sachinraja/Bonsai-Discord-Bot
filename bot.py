import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
import pymongo  

# load environmental variables
load_dotenv()

# MongoDB
MONGODB_URI = os.environ["MONGODB_URI"]
client = pymongo.MongoClient(MONGODB_URI)
db = client["bonsai"]
guild_col = db["guilds"]

TOKEN = os.environ["TOKEN"]

# logging
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# prefixes
prefixes = ["b!"]

def get_prefix(bot, msg):
    guild = guild_col.find_one({"guild_id" : msg.guild.id})

    if guild == None:
        return commands.when_mentioned_or(*prefixes)(bot, msg)
    
    return commands.when_mentioned_or(*guild["prefixes"])(bot, msg)

bot = commands.AutoShardedBot(command_prefix=get_prefix)

bot.remove_command("help")

# all initial cogs for bot
initial_extensions = ["cogs.tree", "cogs.shop", "cogs.inventory", "cogs.balance", "cogs.management"]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}\n{'-' * 20}\n{bot.user.id}")

@bot.command(name="help")
async def help_message(ctx):
    """Sends a list of all the commands and their usage."""

    embed = discord.Embed(title="Help - List of Commands", color=65280)\
        .add_field(name="Argument Definitions", value="Part Type : base, trunk, or leaves.\nMember=optional : If you do not input a member here, it will default to yourself.")\
        .add_field(name="Prefix", value="The default prefix is `b!`. You can change this with the prefix command. You can also call commands by mentioning the bot.")\
        .add_field(name="about", value="Displays a general description of the bot as well as other useful information about it.", inline=False)\
        .add_field(name="balance [Member=optional]", value="Shows your or another user's balance.", inline=False)\
        .add_field(name="buy [Part Name] [Member=optional]", value="Buy part Part Name from Member.", inline=False)\
        .add_field(name="color [Color Hex Code] [Tree Name]", value="Replace the background color of tree Tree Name.", inline=False)\
        .add_field(name="clearinventory", value="Removes all parts from your inventory.", inline=False)\
        .add_field(name="create [Tree Name <= 50 characters]", value="Creates a tree with the name Tree Name.", inline=False)\
        .add_field(name="daily", value="Claim your daily reward ($50-$100).", inline=False)\
        .add_field(name="delete [Tree Name]", value="Deletes the tree Tree Name and returns all its parts to your inventory.", inline=False)\
        .add_field(name="help", value="Displays this message.", inline=False)\
        .add_field(name="inventory [Member=optional]", value="Displays all the parts in your inventory and their corresponding inventory number.", inline=False)\
        .add_field(name="list [Part Type] [Part Name <= 50 characters] [0 < List Price < 10000]", value="List a part for sale in your shop. This must have an attached image to use for the part. Bases must be 15 x 3, trunks must be 15 x 12, and leaves must be 15 x 12.", inline=False)\
        .add_field(name="prefix [New Prefixes]", value="Change the bot's prefixes to New Prefixes on your server. Separate each new prefix with a space.", inline=False)\
        .add_field(name="removeinventory [Inventory Number]", value="Remove part at Inventory Number from your inventory (does not refund any money).", inline=False)\
        .add_field(name="replace [Inventory Number] [Tree Name]", value="Replace a part on tree Tree Name with the part at Inventory Number in your inventory. The old part will return to your inventory.", inline=False)\
        .add_field(name="reset [Tree Name]", value="Reset tree Tree Name to defaults (parts and color). The parts are not returned to your inventory.", inline=False)\
        .add_field(name="shop [Part Type] [Member=optional]", value="Show all the parts that Member has listed as Part Type.", inline=False)\
        .add_field(name="top", value="Shows the users with the top ten balances.", inline=False)\
        .add_field(name="tree [Tree Name]", value="Displays the tree Tree Name.", inline=False)\
        .add_field(name="trees [Member=optional]", value="Displays all of Member's trees.", inline=False)\
        .add_field(name="unlist [Part Name]", value="Unlist part Part Name from your shop.", inline=False)\
        .add_field(name="""rename "[Old Tree Name]" [New Tree Name <= 50 characters]""", value="""Rename the tree Old Tree Name to New Tree Name. Old Tree Name must be surrounded by quotes ("") if there is a space in it.""", inline=False)\
        .add_field(name="visit [Member] [Tree Name]", value="Display Member's tree Tree Name.")

    await ctx.send(embed=embed)

@bot.command(name="about")
async def about_message(ctx):
    """Sends useful information about the bot."""

    embed = discord.Embed(title="About", color=255)\
        .add_field(name="Creator", value="Cloudfox#6783")\
        .add_field(name="Support Server", value="https://discord.gg/YzmSjZz")\
        .add_field(name="GitHub Repository", value="https://github.com/xCloudzx/Bonsai-Discord-Bot")\
        .add_field(name="Description", value="Customize a bonsai tree using items listed by other users. Mix and match bases, trunks, and leaves.", inline=False)

    await ctx.send(embed=embed)

# attempt to load all initial cogs for bot
for extension in initial_extensions:
    try:
        bot.load_extension(extension)
        print(f"Loaded extension {extension}.")
    
    except:
        print(f"Failed to load extension {extension}.")

bot.run(TOKEN)