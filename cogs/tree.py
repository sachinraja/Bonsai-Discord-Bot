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

default_tree = {"base" : {"image" : default_base, "name" : "Default Base", "price" : 0, "creator" : "295014158771159040"}, "trunk" : {"image" : default_trunk, "name" : "Default Trunk", "price" : 0, "creator" : "295014158771159040"}, "leaves" : {"image" : default_leaves, "name" : "Default Leaves", "price" : 0, "creator" : "295014158771159040"}, "background_color" : (0, 0, 255)}
default_trees = (default_tree, default_tree, default_tree)
default_user = {"user_id" : "", "trees" : default_trees, "balance" : 200, "inventory" : [], "parts" : []}

valid_parts = ("base", "trunk", "leaves")

def create_tree_image(user, tree_num):
    """Turns byte data into an image."""

    # save with BytesIO and then paste to image
    tree_to_display = user["trees"][tree_num]
    
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

def create_tree_embed(user, author_name, input_tree_num, tree_num):
    """Creates a generic embed for displaying trees."""

    embed = discord.Embed(title=f"Tree {input_tree_num}", color=25600)\
        .set_author(name=author_name)\
        .add_field(name="Base", value=f"{user['trees'][tree_num]['base']['creator']}'s {user['trees'][tree_num]['base']['name']}")\
        .add_field(name="Trunk", value=f"{user['trees'][tree_num]['trunk']['creator']}'s {user['trees'][tree_num]['trunk']['name']}")\
        .add_field(name="Leaves", value=f"{user['trees'][tree_num]['leaves']['creator']}'s {user['trees'][tree_num]['leaves']['name']}")\
        .set_image(url="attachment://image.png")

    return embed

class Tree(commands.Cog):
    """Commands related to creating trees."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tree")
    async def display_tree(self, ctx, input_tree_num : int):
        """Displays the tree of input_tree_num."""

        if input_tree_num < 1 or input_tree_num > 3:
            await ctx.send("Enter a number from 1 to 3.")
            return

        tree_num = input_tree_num - 1

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)

        im_tree = create_tree_image(user, tree_num)
        embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)

        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name='reset')
    async def reset_tree(self, ctx, input_tree_num : int):
        """Resets the tree of input_tree_num."""

        # check for valid tree
        if input_tree_num < 1 or input_tree_num > 3:
            await ctx.send('Enter a number from 1 to 3.')
            return

        tree_num = input_tree_num - 1

        user = user_col.find_one({'user_id' : ctx.author.id})
        
        if user == None:
            user = default_user
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)

        # Reset tree and update in db
        user['trees'][tree_num] = default_tree
        user_col.update_one({'user_id' : ctx.author.id}, {"$set" : user})

        im_tree = create_tree_image(user, tree_num)
        embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)
        
        await ctx.send(file=im_tree, embed=embed)
    
    @commands.command(name="replace")
    async def replace_part(self, ctx, input_tree_num : int, input_inventory_num : int):
        """Replaces a part of the tree of input_tree_num with the new input_inventory_num."""

        if input_tree_num < 1 or input_tree_num > 3:
            await ctx.send("Enter a number from 1 to 3.")
            return

        tree_num = input_tree_num - 1

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
        
        # get new part from user
        part = user["inventory"].pop(inventory_num)
        
        # set tree part to new part
        part_type = part.pop("type")
        
        # add old part to inventory
        part_for_inventory = user["trees"][tree_num][part_type]
        part_for_inventory["type"] = part_type
        user["inventory"].append(part_for_inventory)

        # add new part to tree
        user["trees"][tree_num][part_type] = part

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        im_tree = create_tree_image(user, tree_num)
        embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)

        await ctx.send(file=im_tree, embed=embed)

    @commands.command(name="color")
    async def change_color(self, ctx, input_tree_num : int, hex_code):
        """Replaces the background color with a new color."""

        if input_tree_num < 1 or input_tree_num > 3:
            await ctx.send('Enter a number from 1 to 3.')
            return

        tree_num = input_tree_num - 1
        
        user = user_col.find_one({'user_id' : ctx.author.id})
        
        if user == None:
            user = default_user
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)
        
        # convert to rgb
        try:
            h = hex_code.lstrip('#')
            user['trees'][tree_num]['background_color'] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        except:
            await ctx.send(f"{hex_code} is not valid.")
            return
        
        user_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

        im_tree = create_tree_image(user, tree_num)
        embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)
        
        await ctx.send(file=im_tree, embed=embed)
    
def setup(bot):
    bot.add_cog(Tree(bot))