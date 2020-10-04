import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import pymongo

# load environmental variables
load_dotenv()

# MongoDB
MONGODB_URI = os.environ["MONGODB_URI"]
client = pymongo.MongoClient(MONGODB_URI)
db = client["bonsai"]
guild_col = db["guilds"]

class Management(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def change_prefix(self, ctx, *, input_prefixes):
        
        prefixes = input_prefixes.split()

        # checks
        if len(prefixes) > 3:
            await ctx.send("You can only have up to 3 prefixes.")
            return

        for prefix in prefixes:
            if len(prefix) > 10:
                await ctx.send(f"{prefix} is over the 10 character limit.")
                return
        
        guild = guild_col.find_one({"guild_id" : ctx.guild.id})

        if guild == None:
            guild = {"guild_id" : ctx.guild.id, "prefixes" : "b!"}
            guild_col.insert_one(guild.copy())
        
        guild["prefixes"] = prefixes
        guild_col.update_one({"guild_id" : ctx.guild.id}, {"$set" : guild})

        prefixes_string = ", ".join(prefixes)
        await ctx.send(f"{ctx.guild} can now use the prefixes {prefixes_string}.")

def setup(bot):
    bot.add_cog(Management(bot))