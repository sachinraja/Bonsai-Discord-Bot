import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image
from random import randint

from utils.default import default_values
from utils.embeds import error_embed, info_embed

# load environmental variables
load_dotenv()

# MongoDB
MONGO_URI = os.environ["MONGO_URI"]
client = pymongo.MongoClient(MONGO_URI)
db = client["bonsai"]
user_col = db["users"]

default_tree, default_user, valid_parts = default_values()

class Balance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="daily")
    @commands.cooldown(1, 60*60*24, commands.BucketType.user)
    async def daily_reward(self, ctx):
        """Get a random amount of money every 24 hours."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        reward = randint(50, 100)
        user["balance"] += reward

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        await ctx.send(embed=info_embed(ctx.author, f"Added ${reward} to your balance! Your new balance is ${user['balance']}."))

    @commands.command(name="balance")
    async def check_balance(self, ctx, member : discord.User = None):
        """Check a player's balance."""

        if member == None:
            member = ctx.author

        user = user_col.find_one({"user_id" : member.id})
        
        if user == None:
            await ctx.send(embed=error_embed(ctx.author, f"{member} does not have a balance yet."))
            return
        
        await ctx.send(embed=info_embed(ctx.author, f"{member} has ${user['balance']}."))

    @commands.command(name="top")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def find_top_balance(self, ctx):
        cursor = user_col.find({}, {"_id" : 0, "user_id" : 1, "balance" : 1}).sort([("balance", pymongo.DESCENDING)]).limit(10)

        top_balances = list(cursor)

        author_balance = user_col.find_one({"user_id" : ctx.author.id}, {"_id" : 0, "balance" : 1})["balance"]
        
        author_position = user_col.find({"balance" : {"$gt" : author_balance}}).count()

        leaderboard = "```prolog\n"
        
        for i, user in enumerate(top_balances):
            username = self.bot.get_user(user["user_id"])
            
            if username == None:
                username = "Unknown User"
            
            leaderboard += f"{i+1}: {username} | ${user['balance']}\n"
        
        leaderboard += "```"

        embed = discord.Embed(title="Top Balances", color=16776960)\
            .add_field(name="Leaderboard", value=leaderboard)\
            .set_footer(text=f"{ctx.author}'s Position: {author_position+1}")
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Balance(bot))