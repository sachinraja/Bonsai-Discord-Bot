import discord
from discord.ext import commands

help_embed = discord.Embed(title="Help - Commands", color=65280)\
    .add_field(name="Prefix", value="The default prefix is `b!`. You can change this with the prefix command. You can also call commands by mentioning the bot.")\
    .add_field(name="Get Started", value="Go [here](https://top.gg/bot/743898864926589029) for more information on how to use the bot and a complete list of commands.")\
    .set_footer(text="Contact the developer if you have any questions: Cloudfox#6783")

about_embed = discord.Embed(title="About", color=255)\
    .add_field(name="Developer", value="Cloudfox#6783")\
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
