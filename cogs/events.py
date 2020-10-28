import discord
from discord.ext import commands

from utils.default import user_col, guild_col, default_user, default_presence
from utils.embeds import error_embed

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # create user in db if there is none
        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        # send error if command fails on argument
        if isinstance(e, commands.BadArgument) or isinstance(e, commands.MissingRequiredArgument):
            await ctx.send(embed=error_embed(ctx.author, e))
        
        # check if command is on cooldown and send time remaining if it is.
        elif isinstance(e, commands.CommandOnCooldown):
            # send time left in seconds if cooldown is under a minute
            if e.retry_after <= 60:
                await ctx.send(embed=error_embed(ctx.author, f"This command is on cooldown, try again in{e.retry_after: .1f} seconds."))
            
            # send time left in hours
            else:
                await ctx.send(embed=error_embed(ctx.author, f"This command is on cooldown, try again in{e.retry_after / 3600: .1f} hours."))

        else:
            print(e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.change_presence(activity=default_presence(self.bot))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # remove from db if removed from guild
        guild_col.find_one_and_delete({"guild_id" : guild.id})
        
        await self.bot.change_presence(activity=default_presence(self.bot))

def setup(bot):
    bot.add_cog(Events(bot))
