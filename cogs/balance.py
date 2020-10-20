import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image
from random import randint

from utils import default
from utils.embeds import error_embed, info_embed

# load environmental variables
load_dotenv()

# MongoDB
MONGO_URI = os.environ["MONGO_URI"]
client = pymongo.MongoClient(MONGO_URI)
db = client["bonsai"]
user_col = db["users"]

default_tree, default_user, valid_parts = default.defaults()

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

    @daily_reward.error
    async def daily_reward_error(self, ctx, error):
        """Reply with a message telling the length of the cooldown for the daily reward command."""
        
        # error message if the command is on cooldown still
        if isinstance(error, commands.CommandOnCooldown):
            # time left on cooldown converted from seconds to hours
            await ctx.send(embed=error_embed(ctx.author, f"This command is on cooldown, try again in{error.retry_after / 3600: .1f} hours."))

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
    async def find_top_balance(self, ctx):
        cursor = user_col.find({}, {"_id" : 0, "user_id" : 1, "balance" : 1}).sort([("balance", pymongo.DESCENDING)]).limit(10)

        top_balances = list(cursor)

        author_balance = user_col.find_one({"user_id" : ctx.author.id}, {"_id" : 0, "balance" : 1})["balance"]
        
        author_position = user_col.find({"balance" : {"$gt" : author_balance}}).count()

        embed = discord.Embed(title="Top Balances", color=16776960)
        for i, user in enumerate(top_balances):
            username = str(self.bot.get_user(user["user_id"]))

            embed = embed.add_field(name="Place", value=i+1)\
                .add_field(name="Name", value=username)\
                .add_field(name="Balance", value=user["balance"])\
                .set_footer(text=f"{ctx.author}'s Position: {author_position+1}")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Balance(bot))