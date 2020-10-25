import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import pymongo

from utils.embeds import error_embed, info_embed

# load environmental variables
load_dotenv()

# MongoDB
MONGO_URI = os.environ["MONGO_URI"]
client = pymongo.MongoClient(MONGO_URI)
db = client["bonsai"]
guild_col = db["guilds"]

class Management(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def change_prefix(self, ctx, *, input_prefixes):
        """Change prefixes on a server."""

        prefixes = input_prefixes.split()

        # checks
        if len(prefixes) > 3:
            await ctx.send(embed=error_embed(ctx.author, "Only 3 prefixes can be entered."))
            return

        for prefix in prefixes:
            if len(prefix) > 10:
                await ctx.send(embed=error_embed(ctx.author, f"`{prefix}` is over the 10 character limit."))
                return
        
        guild = guild_col.find_one({"guild_id" : ctx.guild.id})

        if guild == None:
            guild = {"guild_id" : ctx.guild.id, "prefixes" : "b!"}
            guild_col.insert_one(guild.copy())
        
        guild["prefixes"] = prefixes
        guild_col.update_one({"guild_id" : ctx.guild.id}, {"$set" : guild})

        embed = discord.Embed(title=f"{ctx.guild} Prefixes", color=3138682)

        for i, prefix in enumerate(prefixes):
            embed = embed.add_field(name=f"Prefix {i+1}", value=prefix)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="ping")
    async def get_ping(self, ctx):
        """Send bot's latency."""

        await ctx.send(embed=info_embed(ctx.author, f"Pong: {self.bot.latency * 1000: .2f}ms.", "https://media1.tenor.com/images/a3ca17636f365c6b0a0d11fc6a1240b5/tenor.gif"))

def setup(bot):
    bot.add_cog(Management(bot))