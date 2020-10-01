import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
import pymongo  

# load environmental variables
load_dotenv()
MONGODB_URI = os.environ["MONGODB_URI"]
TOKEN = os.environ["TOKEN"]

# logging
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

bot = commands.AutoShardedBot(command_prefix="b!")
bot.remove_command("help")

# all initial cogs for bot
initial_extensions = ["cogs.tree", "cogs.shop", "cogs.inventory", "cogs.balance"]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}\n{'-' * 20}\n{bot.user.id}")

@bot.command(name="help")
async def help_message(ctx):
    """Sends a list of all the commands and their usage."""

    embed = discord.Embed(title="Help", color=65280)\
        .add_field(name="Argument Definitions", value="Part Type : base, trunk, or leaves.\nMember=optional : If you do not input a member here, it will default to yourself.")\
        .add_field(name="b!about", value="Displays a general description of the bot as well as other useful information about it.", inline=False)\
        .add_field(name="b!balance [Member=optional]", value="Shows your balance or the balance of someone else.", inline=False)\
        .add_field(name="b!buy [Part Name] [Member=optional]", value="Buy a part from Member.", inline=False)\
        .add_field(name="b!color [Color Hex Code] [Tree Name]", value="Replace the background color of a tree.", inline=False)\
        .add_field(name="b!create [Tree Name <= 50 characters]", value="Creates a tree with the name Tree Name.", inline=False)\
        .add_field(name="b!daily", value="Claim your daily reward ($50-$100).", inline=False)\
        .add_field(name="b!help", value="Displays this message.", inline=False)\
        .add_field(name="b!inventory [Member=optional]", value="Displays all the parts in the inventory and their corresponding inventory number.", inline=False)\
        .add_field(name="b!list [Part Type] [Part Name <= 50 characters] [0 < List Price < 10000]", value="List a part for sale. This must have an attached image to use for the part. Bases must be 15 x 3. Trunks must be 15 x 12. Leaves must be 15 x 12.", inline=False)\
        .add_field(name="b!removeinventory [Inventory Number]", value="Remove a part from your inventory (does not refund any money).", inline=False)\
        .add_field(name="b!replace [Inventory Number] [Tree Name]", value="Replace a part on a tree with one in your inventory.", inline=False)\
        .add_field(name="b!reset [Tree Name]", value="Reset a tree to defaults.", inline=False)\
        .add_field(name="b!shop [Part Type] [Member=optional]", value="Show all the parts that Member has listed as Part Type.", inline=False)\
        .add_field(name="b!top", value="Shows the users with the top ten balances.", inline=False)\
        .add_field(name="b!tree [Tree Name]", value="Displays the tree Tree Name.", inline=False)\
        .add_field(name="b!trees [Member=optional]", value="Displays all of Member's trees.", inline=False)\
        .add_field(name="b!unlist [Part Name]", value="Remove a part listed in your shop.", inline=False)\
        .add_field(name="b!visit [Member] [Tree Name]", value="Display Member's tree Tree Name.")

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