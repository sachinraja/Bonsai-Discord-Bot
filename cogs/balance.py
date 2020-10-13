import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image
from random import randint

# load environmental variables
load_dotenv()

# MongoDB
MONGODB_URI = os.environ["MONGODB_URI"]
client = pymongo.MongoClient(MONGODB_URI)
db = client["bonsai"]
user_col = db["users"]

#Create default tree
default_base = None
with open("default_base.png", "rb") as imageFile:
    default_base = imageFile.read()

default_trunk = None
with open("default_trunk.png", "rb") as imageFile:
    default_trunk = imageFile.read()

default_leaves = None
with open("default_leaves.png", "rb") as imageFile:
    default_leaves = imageFile.read()

default_tree = {"name" : "Default Tree", "base" : {"image" : default_base, "name" : "Default Base", "price" : 0, "creator" : "Cloudfox#6783"}, "trunk" : {"image" : default_trunk, "name" : "Default Trunk", "price" : 0, "creator" : "Cloudfox#6783"}, "leaves" : {"image" : default_leaves, "name" : "Default Leaves", "price" : 0, "creator" : "Cloudfox#6783"}, "background_color" : (0, 0, 255)}
default_trees = [default_tree]

default_user = {"user_id" : "", "trees" : default_trees, "balance" : 200, "inventory" : [], "parts" : []}

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

        await ctx.send(f"Added ${reward} to {ctx.author}'s balance! {ctx.author} now have ${user['balance']}.")

    @daily_reward.error
    async def daily_reward_error(self, ctx, error):
        """Reply with a message telling the length of the cooldown for the daily reward command."""
        
        # error message if the command is on cooldown still
        if isinstance(error, commands.CommandOnCooldown):
            # time left on cooldown converted from seconds to hours
            await ctx.send(f"{ctx.author} this command is on cooldown for you, try again in{error.retry_after / 3600: .1f} hours.")

    @commands.command(name="balance")
    async def check_balance(self, ctx, member : discord.User = None):
        """Check a player's balance."""

        if member == None:
            member = ctx.author

        user = user_col.find_one({"user_id" : member.id})
        
        if user == None:
            await ctx.send(f"{member} does not have any trees.")
            return
        
        await ctx.send(f"{member} has ${user['balance']}.")

    @commands.command(name="top")
    async def find_top_balance(self, ctx):
        cursor = user_col.find({}).sort([("balance", pymongo.DESCENDING)]).limit(10)

        top_balances = list(cursor)

        embed = discord.Embed(title="Top Balances", color=16776960)
        for i, user in enumerate(top_balances):
            username = str(self.bot.get_user(user["user_id"]))

            embed = embed.add_field(name="Place", value=i+1)\
                .add_field(name="Name", value=username)\
                .add_field(name="Balance", value=user["balance"])
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Balance(bot))