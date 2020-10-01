import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image

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

valid_parts = ("base", "trunk", "leaves")

def find_tree(user, input_tree_name):
    """Loop over trees and find one based on the name. Return tree."""

    tree_to_display = None
    tree_name = input_tree_name.lower()

    for tree in user["trees"]:
        if tree["name"].lower() == tree_name:
            tree_to_display = tree
            break
    
    if tree_to_display == None:
        return None
    
    return tree_to_display

def find_tree_index(user, input_tree_name):
    """Loop over trees and find one based on the name. Return tree index."""

    tree_to_display = None
    tree_name = input_tree_name.lower()

    for i, tree in enumerate(user["trees"]):
        if tree["name"].lower() == tree_name:
            tree_to_display = tree
            break
    
    if tree_to_display == None:
        return None
    
    return i

def create_tree_image(user, tree_to_display):
    """Turns byte data into an image."""
    
    # save with BytesIO and then paste to image
    base_image = Image.open(BytesIO(tree_to_display["base"]["image"]))
    trunk_image = Image.open(BytesIO(tree_to_display["trunk"]["image"]))
    leaves_image = Image.open(BytesIO(tree_to_display["leaves"]["image"]))
    
    tree_image = Image.new("RGB", (15, 15), tuple(tree_to_display["background_color"]))
    tree_image.paste(base_image, (0, 12), mask=base_image)
    tree_image.paste(trunk_image, mask=trunk_image)
    tree_image.paste(leaves_image, mask=leaves_image)
    
    # resize tree so user can see it
    tree_image = tree_image.resize((tree_image.size[0] * 10, tree_image.size[1] * 10), resample=Image.NEAREST)

    # save with BytesIO to send as embed in discord
    with BytesIO() as image_binary:
        tree_image.save(image_binary, "PNG")
        image_binary.seek(0)
        im_tree = discord.File(fp=image_binary, filename="image.png")
        return im_tree

def create_tree_embed(user, author_name, tree_to_display):
    """Creates a generic embed for displaying trees."""
        
    embed = discord.Embed(title=tree_to_display["name"], color=25600)\
        .set_author(name=author_name)\
        .add_field(name="Base", value=f"{tree_to_display['base']['creator']}'s {tree_to_display['base']['name']}")\
        .add_field(name="Trunk", value=f"{tree_to_display['trunk']['creator']}'s {tree_to_display['trunk']['name']}")\
        .add_field(name="Leaves", value=f"{tree_to_display['leaves']['creator']}'s {tree_to_display['leaves']['name']}")\
        .set_image(url="attachment://image.png")

    return embed

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
            await ctx.send(f"{ctx.author} does not have a tree with the name {input_tree_name}.")
            return

        im_tree = create_tree_image(user, tree_to_display)
        embed = create_tree_embed(user, ctx.author.name, tree_to_display)

        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="visit")
    async def view_other_tree(self, ctx, member : discord.Member, *, input_tree_name):
        """Displays the tree of input_tree_name of a certain member."""
        
        user = user_col.find_one({"user_id" : member.id})
        
        if user == None:
            ctx.send(f"{member} does not have any trees.")
            return

        tree_to_display = find_tree(user, input_tree_name)
            
        if tree_to_display == None:
            await ctx.send(f"{member} does not have a tree with the name {input_tree_name}.")
            return

        im_tree = create_tree_image(user, tree_to_display)
        embed = create_tree_embed(user, ctx.author.name, tree_to_display)

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
            await ctx.send("Tree Name cannot be over 50 characters long.")
            return
        
        if len(user["trees"]) >= 3:
            await ctx.send("You are already at the max number of trees! If you want to reset a tree, use the command b!reset [Tree Name].")
            return
        
        if find_tree(user, input_tree_name) != None:
            await ctx.send(f"A tree with the name {input_tree_name} already exists.")
            return
        
        new_tree = default_tree.copy()
        new_tree["name"] = input_tree_name
        user["trees"].append(new_tree)

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})
        
        tree_to_display = find_tree(user, input_tree_name)
            
        if tree_to_display == None:
            await ctx.send(f"You do not have a tree with the name {input_tree_name}.")
            return

        im_tree = create_tree_image(user, tree_to_display)
        embed = create_tree_embed(user, ctx.author.name, tree_to_display)
        
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
            await ctx.send(f"You do not have a tree with the name {input_tree_name}.")
            return

        # Reset tree and update in db
        tree_for_name = find_tree(user, input_tree_name)

        user["trees"][tree_index] = default_tree.copy()
        user["trees"][tree_index]["name"] = tree_for_name["name"]

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        tree_to_display = find_tree(user, input_tree_name)

        im_tree = create_tree_image(user, tree_to_display)
        embed = create_tree_embed(user, ctx.author.name, tree_to_display)
        
        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="trees")
    async def list_trees(self, ctx, member : discord.Member = None):
        """List all the trees of member."""
        
        if member == None:
            member = ctx.author
        
        user = user_col.find_one({"user_id" : member.id})
        
        if user == None:
            await ctx.send(f"{member} has no trees.")
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
            await ctx.send(f"There is no part at inventory #{input_inventory_num}.")
            return
        
        inventory_num = input_inventory_num - 1

        if input_inventory_num <= 0:
            await ctx.send(f"Inventory numbers must be over 0.")
            return
        
        elif len(user["inventory"]) - 1 < inventory_num:
            await ctx.send(f"Your inventory only goes up to {len(user['inventory'])}, but you entered #{input_inventory_num}.")
            return
        
        tree_index = find_tree_index(user, input_tree_name)
        
        if tree_index == None:
            await ctx.send(f"You do not have a tree with the name {input_tree_name}.")
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
        embed = create_tree_embed(user, ctx.author.name, tree_to_display)

        await ctx.send(file=im_tree, embed=embed)

    @commands.command(name="color")
    async def change_color(self, ctx, hex_code, *, input_tree_name):
        """Replaces the background color with a new color."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        tree_index = find_tree_index(user, input_tree_name)

        if tree_index == None:
            await ctx.send(f"You do not have a tree with the name {input_tree_name}.")
            return

        # convert to rgb
        try:
            h = hex_code.lstrip("#")
            user["trees"][tree_index]["background_color"] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        except:
            await ctx.send(f"{hex_code} is not valid.")
            return
        
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        tree_to_display = find_tree(user, input_tree_name)

        im_tree = create_tree_image(user, tree_to_display)
        embed = create_tree_embed(user, ctx.author.name, tree_to_display)
        
        await ctx.send(file=im_tree, embed=embed)
    
def setup(bot):
    bot.add_cog(Tree(bot))