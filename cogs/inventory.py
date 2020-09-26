import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import pymongo
import asyncio
from math import ceil

# load environmental variables
load_dotenv()

# MongoDB
MONGODB_URI = os.environ["MONGODB_URI"]
client = pymongo.MongoClient(MONGODB_URI)
db = client["bonsai"]
user_col = db["users"]

class Inventory(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="inventory")
    async def list_inventory(self, ctx, member : discord.Member = None):
        """Lists the entire inventory 25 items at a time."""

        if member == None:
            member = ctx.author
        
        user = user_col.find_one({'user_id' : member.id})

        if user == None:
            ctx.send(f"{member} has no parts in their inventory.")
            return

        embed = discord.Embed(title=f"{member}'s Inventory", color=255)
        
        i = 1
        for part in user['inventory'][:26]:
            embed = embed.add_field(name=part['type'], value=f"{i} : {part['creator']}'s {part['name']}", inline=False)

            i += 1

        inventory_message = await ctx.send(embed=embed)

        # only one page needs to be displayed
        if len(user['inventory']) <= 25:
            return
        
        await inventory_message.add_reaction('⬅️')
        await inventory_message.add_reaction('➡️')

        def check(reaction, user):
            return reaction.message.id == inventory_message.id and user.id == ctx.author.id and str(reaction.emoji) in ['⬅️', '➡️']

        total_part_lists = ceil(len(user['inventory']) / 25)
        current_part_list = 1

        while True:
            try:
                reaction, reaction_user = await self.bot.wait_for('reaction_add', check=check, timeout=300)

                # check for arrow reactions
                if str(reaction.emoji) == '⬅️' and current_part_list > 1:
                    current_part_list -= 1

                    inventory_index_first = (current_part_list - 1) * 25
                    inventory_index_last = (current_part_list * 25) + 1

                    embed = discord.Embed(title=f"{member}'s Inventory Page {current_part_list}", color=255)
                    
                    j = inventory_index_first
                    for part in user['inventory'][inventory_index_first:inventory_index_last]:
                        embed = embed.add_field(name=part['type'], value=f"{j+1} : {part['creator']}'s {part['name']}", inline=False)
                        j += 1

                    await inventory_message.edit(embed=embed)
                    await inventory_message.remove_reaction(reaction, reaction_user)

                elif str(reaction.emoji) == '➡️' and current_part_list < total_part_lists:
                    current_part_list += 1

                    inventory_index_first = (current_part_list - 1) * 25
                    inventory_index_last = (current_part_list * 25) + 1
                    
                    embed = discord.Embed(title=f"{member}'s Inventory Page {current_part_list}", color=255)
                    
                    j = inventory_index_first
                    for part in user['inventory'][inventory_index_first:inventory_index_last]:
                        embed = embed.add_field(name=part['type'], value=f"{j+1} : {part['creator']}'s {part['name']}", inline=False)
                        j += 1

                    await inventory_message.edit(embed=embed)
                    await inventory_message.remove_reaction(reaction, reaction_user)

            except asyncio.TimeoutError:
                break

    @commands.command(name="removeinventory")
    async def delete_inventory_part(self, ctx, input_inventory_num : int):
        """Delete a part from the inventory."""

        user = user_col.find_one({'user_id' : ctx.author.id})
        
        if user == None:
            await ctx.send(f'There is no part at inventory #{input_inventory_num}.')
            return
        
        inventory_num = input_inventory_num - 1

        # check for proper inventory number
        if input_inventory_num <= 0:
            await ctx.send(f'Inventory numbers must be over 0.')
            return
        
        elif len(user['inventory']) - 1 < inventory_num:
            await ctx.send(f"Your inventory only goes up to {len(user['inventory'])}, but you entered #{input_inventory_num}.")
            return
        
        user['inventory'].pop(inventory_num)
        user_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

        await ctx.send(f"Part at #{input_inventory_num} has been removed.")

def setup(bot):
    bot.add_cog(Inventory(bot))