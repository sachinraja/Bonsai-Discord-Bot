import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image
import asyncio
from math import ceil

from utils.image import binary_to_file
from utils.embeds import inventory_part_embed, error_embed, info_embed
 
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
    async def list_inventory(self, ctx, input_inventory_num : int = None):
        """Lists the entire inventory 25 items at a time."""
        
        user = user_col.find_one({"user_id" : ctx.author.id})

        if user == None or len(user["inventory"]) == 0:
            await ctx.send(embed=error_embed(ctx.author, "You have no parts in your inventory."))
            return

        # information on specific part
        if input_inventory_num != None:

            inventory_num = input_inventory_num - 1
            
            # check for proper inventory number
            if input_inventory_num <= 0:
                await ctx.send(embed=error_embed(ctx.author, "Inventory numbers must be over 0."))
                return
            
            elif len(user["inventory"]) - 1 < inventory_num:
                await ctx.send(embed=error_embed(ctx.author, f"Your inventory only goes up to {len(user['inventory'])}, but #{input_inventory_num} was entered."))
                return
            
            inventory_part = user["inventory"][inventory_num]
            part_picture = binary_to_file(inventory_part["image"])
            embed = inventory_part_embed(inventory_part, inventory_part["creator"])

            await ctx.send(file=part_picture, embed=embed)
            return

        embed = discord.Embed(title=f"{ctx.author}'s Inventory", color=255)
        
        total_part_lists = ceil(len(user["inventory"]) / 25)

        i = 1
        for part in user["inventory"][:26]:
            embed = embed.add_field(name=part["type"], value=f"{i} : {part['creator']}'s {part['name']}", inline=False)\
                .set_footer(text=f"Page 1 / {total_part_lists}")


            i += 1

        inventory_message = await ctx.send(embed=embed)

        # only one page needs to be displayed
        if len(user["inventory"]) <= 25:
            return
        
        await inventory_message.add_reaction("⬅️")
        await inventory_message.add_reaction("➡️")

        def check(reaction, user):
            return reaction.message.id == inventory_message.id and user.id == ctx.author.id and str(reaction.emoji) in ["⬅️", "➡️"]

        current_part_list = 1

        while True:
            try:
                reaction, reaction_user = await self.bot.wait_for("reaction_add", check=check, timeout=300)

                # check for arrow reactions
                if str(reaction.emoji) == "⬅️" and current_part_list > 1:
                    current_part_list -= 1

                    inventory_index_first = (current_part_list - 1) * 25
                    inventory_index_last = (current_part_list * 25) + 1

                    embed = discord.Embed(title=f"{ctx.author}'s Inventory", color=255)\
                        .set_footer(text=f"Page {current_part_list} / {total_part_lists}")
                    
                    j = inventory_index_first
                    for part in user["inventory"][inventory_index_first:inventory_index_last]:
                        embed = embed.add_field(name=part["type"], value=f"{j+1} : {part['creator']}'s {part['name']}", inline=False)
                        j += 1

                    await inventory_message.edit(embed=embed)
                    await inventory_message.remove_reaction(reaction, reaction_user)

                elif str(reaction.emoji) == "➡️" and current_part_list < total_part_lists:
                    current_part_list += 1

                    inventory_index_first = (current_part_list - 1) * 25
                    inventory_index_last = (current_part_list * 25) + 1
                    
                    embed = discord.Embed(title=f"{ctx.author}'s Inventory", color=255)\
                        .set_footer(text=f"Page {current_part_list} / {total_part_lists}")
                    
                    j = inventory_index_first
                    for part in user["inventory"][inventory_index_first:inventory_index_last]:
                        embed = embed.add_field(name=part["type"], value=f"{j+1} : {part['creator']}'s {part['name']}", inline=False)
                        j += 1

                    await inventory_message.edit(embed=embed)
                    await inventory_message.remove_reaction(reaction, reaction_user)

            except asyncio.TimeoutError:
                break

    @commands.command(name="removeinventory")
    async def delete_inventory_part(self, ctx, input_inventory_num : int):
        """Delete a part from the inventory."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            await ctx.send(embed=error_embed(ctx.author, f"There is no part in your inventory at #{input_inventory_num}."))
            return
        
        inventory_num = input_inventory_num - 1

        # check for proper inventory number
        if input_inventory_num <= 0:
            await ctx.send(embed=error_embed(ctx.author, "Inventory numbers must be over 0."))
            return
        
        elif len(user["inventory"]) - 1 < inventory_num:
            await ctx.send(embed=error_embed(ctx.author, f"Your inventory only goes up to {len(user['inventory'])}, but #{input_inventory_num} was entered."))
            return
        
        user["inventory"].pop(inventory_num)
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        await ctx.send(embed=info_embed(ctx.author, f"Part at #{input_inventory_num} has been removed."))

    @commands.command(name="clearinventory")
    async def clear_inventory(self, ctx):
        """Deletes all of the parts in the inventory."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            await ctx.send(embed=info_embed(ctx.author, "Cleared your inventory."))
            return

        user["inventory"].clear()
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        await ctx.send(embed=info_embed(ctx.author, "Cleared your inventory."))

def setup(bot):
    bot.add_cog(Inventory(bot))