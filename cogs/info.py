import discord
from discord.ext import commands

help_embed = discord.Embed(title="Help - List of Commands", color=65280)\
    .add_field(name="Argument Definitions", value="""Part Type : base, trunk, or leaves.\nMember=optional : If you do not input a member here, it will default to yourself. If Member has spaces in it, you must surround it in quotation marks: "Cloud Fox#6783" """)\
    .add_field(name="Prefix", value="The default prefix is `b!`. You can change this with the prefix command. You can also call commands by mentioning the bot.")\
    .add_field(name="Get Started", value="Go [here](https://top.gg/bot/743898864926589029) for more information on how to use the bot.")\
    .add_field(name="about", value="Displays a general description of the bot as well as other useful information about it.", inline=False)\
    .add_field(name="balance [Member=optional]", value="Shows your or another user's balance.", inline=False)\
    .add_field(name="buy [Part Name] [Member=optional]", value="Buy part Part Name from Member.", inline=False)\
    .add_field(name="color [Color Hex Code] [Tree Name]", value="Replace the background color of tree Tree Name.", inline=False)\
    .add_field(name="clearinventory", value="Removes all parts from your inventory.", inline=False)\
    .add_field(name="create [Tree Name <= 50 characters]", value="Creates a tree with the name Tree Name.", inline=False)\
    .add_field(name="daily", value="Claim your daily reward ($50-$100).", inline=False)\
    .add_field(name="delete [Tree Name]", value="Deletes the tree Tree Name and returns all its parts to your inventory.", inline=False)\
    .add_field(name="help", value="Displays this message.", inline=False)\
    .add_field(name="inventory [Inventory Number=Optional]", value="Displays all the parts in your inventory and their corresponding inventory number. If an Inventory Number is entered, information for that specific part will be displayed.", inline=False)\
    .add_field(name="list [Part Type] [Part Name <= 50 characters] [0 < List Price < 10000]", value="List a part for sale in your shop. This must have an attached image to use for the part. Bases must be 15 x 3, trunks must be 15 x 12, and leaves must be 15 x 12.", inline=False)\
    .add_field(name="prefix [New Prefixes]", value="Change the bot's prefixes to New Prefixes on your server. Separate each new prefix with a space.", inline=False)\
    .add_field(name="removeinventory [Inventory Number]", value="Remove part at Inventory Number from your inventory (does not refund any money).", inline=False)\
    .add_field(name="""rename "[Old Tree Name]" [New Tree Name <= 50 characters]""", value="""Rename the tree Old Tree Name to New Tree Name. Old Tree Name must be surrounded by quotes ("") if there is a space in it.""", inline=False)\
    .add_field(name="replace [Inventory Number] [Tree Name]", value="Replace a part on tree Tree Name with the part at Inventory Number in your inventory. The old part will return to your inventory.", inline=False)\
    .add_field(name="reset [Tree Name]", value="Reset tree Tree Name to defaults (parts and color). The parts are not returned to your inventory.", inline=False)\
    .add_field(name="shop [Part Type] [Member=optional]", value="Show all the parts that Member has listed as Part Type.", inline=False)\
    .add_field(name="top", value="Shows the users with the top ten balances.", inline=False)\
    .add_field(name="tree [Tree Name]", value="Displays the tree Tree Name.", inline=False)\
    .add_field(name="trees [Member=optional]", value="Displays all of Member's trees.", inline=False)\
    .add_field(name="unlist [Part Name]", value="Unlist part Part Name from your shop.", inline=False)\
    .add_field(name="visit [Member] [Tree Name]", value="Display Member's tree Tree Name.")

about_embed = discord.Embed(title="About", color=255)\
    .add_field(name="Creator", value="Cloudfox#6783")\
    .add_field(name="Support Server", value="https://discord.gg/tNC22WD")\
    .add_field(name="GitHub Repository", value="https://github.com/xCloudzx/Bonsai-Discord-Bot")\
    .add_field(name="Invite Link", value="[Invite Bot to Your Server](https://discord.com/oauth2/authorize?client_id=743898864926589029&permissions=8192&scope=bot)")\
    .add_field(name="Description", value="Customize a bonsai tree using items listed by other users. Mix and match bases, trunks, and leaves.", inline=False)

class Info(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_message(self, ctx):
        """Sends a list of all the commands and their usage."""

        await ctx.send(embed=help_embed)

    @commands.command(name="about")
    async def about_message(self, ctx):
        """Sends useful information about the bot."""

        await ctx.send(embed=about_embed)

def setup(bot):
    bot.add_cog(Info(bot))
