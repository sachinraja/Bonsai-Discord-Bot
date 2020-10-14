import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from io import BytesIO
import pymongo
from PIL import Image
import requests
import asyncio

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

def binary_to_embed(binary):
    part_image = Image.open(BytesIO(binary))
    part_image = part_image.resize((part_image.size[0] * 10, part_image.size[1] * 10), Image.NEAREST)

    with BytesIO() as image_binary:
        part_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        im_part = discord.File(fp=image_binary, filename='image.png')
        return im_part

def part_embed(parts, parts_index, username):
    return discord.Embed(title=f"{parts[parts_index]['type']} Listing {parts_index+1}", color=255)\
            .set_author(name=username)\
            .add_field(name="Name", value=parts[parts_index]["name"])\
            .add_field(name="List Price", value=parts[parts_index]["price"])\
            .set_image(url="attachment://image.png")

async def check_attachment(ctx, width, height):
    # check for attachment on message
    if len(ctx.message.attachments) == 0:
        await ctx.send(f"{ctx.author}, attach an image ending with jpg, jpeg, or png.")
        return False
    
    # check for correct extension on attachment
    pic_ext = [".jpg", ".jpeg", ".png"]
    match = False
    for ext in pic_ext:
        if ctx.message.attachments[0].filename.endswith(ext):
            match = True
    
    if match == False:
        await ctx.send(f"{ctx.author} the image must end with jpg, jpeg, or png.")
        return False

    # check for correct size
    if ctx.message.attachments[0].width != width or ctx.message.attachments[0].height != height:
        await ctx.send(f"{ctx.author}, wrong size: ({ctx.message.attachments[0].width} x {ctx.message.attachments[0].height})! The image must be {width} x {height}.")
        return False

class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="list")
    async def create_part_listing(self, ctx, part_type, part_name, list_price : int):
        """List a part on the player's shop."""

        part_type = part_type.lower()
        if part_type not in valid_parts:
            await ctx.send(f"{ctx.author}, enter base, trunk, or leaves.")
            return
        
        if len(part_name) > 50:
            await ctx.send(f"{ctx.author}, Part Name cannot be over 50 characters long.")
            return
        
        if list_price < 0 or list_price > 10000:
            await ctx.send(f"{ctx.author}, List Price cannot be less than $0 or over $10,000.")
            return
        
        if part_type == "base" and await check_attachment(ctx, 15, 3) == False:
            return

        elif part_type in ["trunk", "leaves"] and await check_attachment(ctx, 15, 12) == False:
            return

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)

        parts = user["parts"]

        if len(parts) >= 15:
            await ctx.send(f"{ctx.author}, you have exceeded your limit of 15 parts.")
            return

        for part in parts:
            if part["name"].lower() == part_name.lower():
                await ctx.send(f"{ctx.author}, you have already listed a part with the name {part['name']}.")
                return

        attachment_url = ctx.message.attachments[0].url
        file_request = requests.get(attachment_url)
        parts.append({"image" : file_request.content, "name" : part_name, "type" : part_type, "price" : list_price})

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        im_part = binary_to_embed(file_request.content)

        embed = discord.Embed(title=f"New {part_type} Listing", color=255)\
            .set_author(name= str(ctx.author))\
            .add_field(name="Name", value=part_name)\
            .add_field(name="List Price", value=list_price)\
            .set_image(url="attachment://image.png")

        await ctx.send(file=im_part, embed=embed)

    @commands.command("unlist")
    async def delete_part_listing(self, ctx, part_name):
        """Delete a listing from the player's shop."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            await ctx.send(f"{ctx.author} does not have any parts listed.")
            return
        
        part_for_removal = None
        for i, part in enumerate(user["parts"]):
            if part["name"].lower() == part_name.lower():
                part_for_removal = part["name"]
                break
        
        if part_for_removal == None:
            await ctx.send(f"{ctx.author}, part {part_name} was not found.")
            return
        
        user["parts"].pop(i)
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        await ctx.send(f"Unlisted {ctx.author}'s part {part_for_removal}.")
        
    @commands.command(name="shop")
    async def shop_parts(self, ctx, part_type, member : discord.User = None):
        """View all the parts in a player's shop."""

        part_type = part_type.lower()
        if part_type not in valid_parts:
            await ctx.send(f"{ctx.author}, enter base, trunk, or leaves.")
            return

        if member == None:
            member = ctx.author
        
        seller = user_col.find_one({"user_id" : member.id})
        
        if seller == None:
            await ctx.send(f"{member} has no parts listed.")
            return
            
        all_parts = seller["parts"]
        
        parts = []
        for part in all_parts:
            if part["type"] == part_type:
                parts.append(part)
        
        if len(parts) == 0:
            await ctx.send(f"{member} has none of those listed.")
            return

        part_picture = binary_to_embed(parts[0]["image"])

        embed = part_embed(parts, 0, str(member))
        
        shop_message = await ctx.send(file=part_picture, embed=embed)

        if len(parts) == 1:
            return
        
        await shop_message.add_reaction("⬅️")
        await shop_message.add_reaction("➡️")

        def check(reaction, user):
            return reaction.message.id == shop_message.id and user.id == ctx.author.id and str(reaction.emoji) in ["⬅️", "➡️"]

        total_parts = len(parts) - 1
        current_part = 0

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300)

                # check for arrow reactions
                if str(reaction.emoji) == "⬅️" and current_part != 0:
                    current_part -= 1
                    
                    part_picture = binary_to_embed(parts[current_part]["image"])

                    embed = part_embed(parts, current_part, str(member))
                    
                    await shop_message.delete()
                    shop_message = await ctx.send(file=part_picture, embed=embed)
                    await shop_message.add_reaction("⬅️")
                    await shop_message.add_reaction("➡️")

                elif str(reaction.emoji) == "➡️" and current_part != total_parts:
                    
                    current_part += 1

                    part_picture = binary_to_embed(parts[current_part]["image"])

                    embed = part_embed(parts, current_part, str(member))

                    await shop_message.delete()
                    shop_message = await ctx.send(file=part_picture, embed=embed)
                    await shop_message.add_reaction("⬅️")
                    await shop_message.add_reaction("➡️")

            except asyncio.TimeoutError:
                break
        
    @commands.command(name="buy")
    async def buy_part(self, ctx, part_name, member : discord.User = None):
        """Buy a part from a player's shop."""

        user = user_col.find_one({"user_id" : ctx.author.id})
        
        if user == None:
            user = default_user.copy()
            user["user_id"] = ctx.author.id
            user_col.insert_one(user)

        if len(user["inventory"]) >= 100:
            await ctx.send(f"{ctx.author}, you have reached the limit of 100 parts in your inventory.")
            return
        
        if member == None:
            member = ctx.author
        
        seller = user_col.find_one({"user_id" : member.id})

        if seller == None:
            await ctx.send(f"{member} has no parts listed.")
            return

        # get correct spelling of list in seller
        all_parts = seller["parts"]
        part_to_buy = None

        for part in all_parts:
            if part["name"].lower() == part_name.lower():
                part_to_buy = part
        
        if part_to_buy == None:
            await ctx.send(f"{member} does not have a part named {part_name}.")
            return
        
        if part_to_buy["price"] > user["balance"]:
            await ctx.send(f"{ctx.author}, you only have ${user['balance']}, but {part_to_buy['name']} costs ${part_to_buy['price']}.")
            return
        
        # give part and remove money from user
        part_to_buy["creator"] = str(member)
        user["inventory"].append(part_to_buy)
        user["balance"] -= part_to_buy["price"]
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        # give money to seller
        seller_tree_account = user_col.find_one({"user_id" : member.id})
        seller_tree_account["balance"] += part_to_buy["price"]
        user_col.update_one({"user_id" : member.id}, {"$set" : seller_tree_account})

        await ctx.send(f"{ctx.author} bought {member}'s {part_to_buy['name']}.")

def setup(bot):
    bot.add_cog(Shop(bot))