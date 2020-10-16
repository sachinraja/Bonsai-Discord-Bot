import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image

from utils import default
from utils.find import find_tree, find_tree_index
from utils.image import create_tree_image
from utils.embeds import tree_embed, error_embed, info_embed

# load environmental variables
load_dotenv()

# MongoDB
MONGODB_URI = os.environ["MONGODB_URI"]
client = pymongo.MongoClient(MONGODB_URI)
db = client["bonsai"]
user_col = db["users"]

default_tree, default_user, valid_parts = default.defaults()

class Tree(commands.Cog):
    """Commands related to creating trees."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tree")
    async def display_tree(self, ctx, *, input_tree_name):
        """Displays the tree of input_tree_name."""
        
        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)

        tree_to_display = find_tree(user, input_tree_name)
            
        if tree_to_display == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, ctx.author, tree_to_display)

        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="visit")
    async def view_other_tree(self, ctx, member : discord.User, *, input_tree_name):
        """Displays the tree of input_tree_name of a certain member."""
        
        user = user_col.find_one({"user_id" : member.id})
        
        if user == None:
            await ctx.send(embed=error_embed(ctx.author, f"{member} does not have any trees."))
            return

        tree_to_display = find_tree(user, input_tree_name)
            
        if tree_to_display == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, member, tree_to_display)

        await ctx.send(file=im_tree, embed=embed)

    @commands.command(name="create")
    async def create_tree(self, ctx, *, input_tree_name):
        """Creates a new tree."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        if len(input_tree_name) > 50:
            await ctx.send(embed=error_embed(ctx.author, "Tree Name cannot be over 50 characters long."))
            return
        
        if len(user["trees"]) >= 3:
            await ctx.send(embed=error_embed(ctx.author, "You are already at the max number of trees! To reset a tree, use the reset [Tree Name] command. To delete a tree, use the delete [Tree Name] command."))
            return
        
        if find_tree(user, input_tree_name) != None:
            await ctx.send(embed=error_embed(ctx.author, f"A tree with the name {input_tree_name} already exists."))
            return
        
        new_tree = default_tree.copy()
        new_tree["name"] = input_tree_name
        user["trees"].append(new_tree)

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})
        
        tree_to_display = find_tree(user, input_tree_name)
            
        if tree_to_display == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, ctx.author, tree_to_display)
        
        await ctx.send(file=im_tree, embed=embed)

    @commands.command(name="reset")
    async def reset_tree(self, ctx, *, input_tree_name):
        """Resets the tree of input_tree_name."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        tree_index = find_tree_index(user, input_tree_name)

        if tree_index == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return

        # Reset tree and update in db
        tree_for_name = find_tree(user, input_tree_name)

        user["trees"][tree_index] = default_tree.copy()
        user["trees"][tree_index]["name"] = tree_for_name["name"]

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        tree_to_display = find_tree(user, input_tree_name)

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, ctx.author, tree_to_display)
        
        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="trees")
    async def list_trees(self, ctx, member : discord.User = None):
        """List all the trees of member."""
        
        if member == None:
            member = ctx.author
        
        user = user_col.find_one({"user_id" : member.id})
        
        if user == None:
            await ctx.send(embed=error_embed(ctx.author, f"{member} has no trees."))
            return
        
        embed = discord.Embed(title=f"{member}'s Trees", color=0o05300)
        for tree in user["trees"]:
            embed = embed.add_field(name=tree['name'], value=f"""Base: {tree["base"]["creator"]}'s {tree["base"]["name"]}\n
            Trunk: {tree["trunk"]["creator"]}'s {tree["trunk"]["name"]}\n
            Leaves: {tree["leaves"]["creator"]}'s {tree["leaves"]["name"]}\n""")

        await ctx.send(embed=embed)

    @commands.command(name="replace")
    async def replace_part(self, ctx, input_inventory_num : int, *, input_tree_name):
        """Replaces a part of the tree of input_tree_name with the new input_inventory_num."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            await ctx.send(embed=error_embed(ctx.author, f"There is no part in your inventory at #{input_inventory_num}."))
            return
        
        inventory_num = input_inventory_num - 1

        if input_inventory_num <= 0:
            await ctx.send(embed=error_embed(ctx.author, "Inventory numbers must be over 0."))
            return
        
        elif len(user["inventory"]) - 1 < inventory_num:
            await ctx.send(embed=error_embed(ctx.author, f"Your inventory only goes up to {len(user['inventory'])}, but #{input_inventory_num} was entered."))
            return
        
        tree_index = find_tree_index(user, input_tree_name)
        
        if tree_index == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return
        
        # get new part from user
        part = user["inventory"].pop(inventory_num)
        
        # set tree part to new part
        part_type = part.pop("type")
        
        # add old part to inventory
        part_for_inventory = user["trees"][tree_index][part_type]
        part_for_inventory["type"] = part_type
        user["inventory"].append(part_for_inventory)

        # add new part to tree
        user["trees"][tree_index][part_type] = part

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        tree_to_display = find_tree(user, input_tree_name)

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, ctx.author, tree_to_display)

        await ctx.send(file=im_tree, embed=embed)

    @commands.command(name="color", aliases=["colour"])
    async def change_color(self, ctx, hex_code, *, input_tree_name):
        """Replaces the background color with a new color."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        tree_index = find_tree_index(user, input_tree_name)

        if tree_index == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return

        # convert to rgb
        try:
            h = hex_code.lstrip("#")
            user["trees"][tree_index]["background_color"] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        except:
            await ctx.send(embed=error_embed(ctx.author, f"{hex_code} is not valid."))
            return
        
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        tree_to_display = find_tree(user, input_tree_name)

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, ctx.author, tree_to_display)
        
        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="rename")
    async def rename_tree(self, ctx, input_tree_name, *, new_name):
        """Rename tree of input_tree_name."""
        
        if len(new_name) > 50:
            await ctx.send(embed=error_embed(ctx.author, "Tree Name cannot be over 50 characters long."))
            return

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        tree_index = find_tree_index(user, input_tree_name)

        if tree_index == None:
           await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
           return
        
        user["trees"][tree_index]["name"] = new_name
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        tree_to_display = find_tree(user, new_name)

        im_tree = create_tree_image(user, tree_to_display)
        embed = tree_embed(user, ctx.author, tree_to_display)
        
        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="delete")
    async def delete_tree(self, ctx, *, input_tree_name):
        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        tree_index = find_tree_index(user, input_tree_name)

        if tree_index == None:
            await ctx.send(embed=error_embed(ctx.author, f"You do not have a tree with the name {input_tree_name}."))
            return

        # get parts and move to inventory
        tree_name_output = user["trees"][tree_index]["name"]

        # iterate over tree to return parts to inventory
        inventory_parts = []
        for key, value in user["trees"][tree_index].items():
            if key == "name" or key == "background_color":
                continue
            
            part_for_inventory = value
            part_for_inventory["type"] = key
            inventory_parts.append(part_for_inventory)
        
        # add old part to inventory
        user["inventory"].extend(inventory_parts)
            
        # delete tree
        user["trees"].pop(tree_index)
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})
        
        await ctx.send(embed=info_embed(ctx.author, f"Deleted tree {tree_name_output}."))



def setup(bot):
    bot.add_cog(Tree(bot))