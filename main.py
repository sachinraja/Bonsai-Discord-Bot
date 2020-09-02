import discord
from discord.ext import commands
import logging
import os
from PIL import Image
from dotenv import load_dotenv
import pymongo
import never_sleep
import base64
from io import BytesIO
import requests

# load token
load_dotenv()
TOKEN = os.environ['TOKEN']
DBUSERNAME = os.environ['DBUSERNAME']
DBPASS = os.environ['DBPASS']
# logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix='b!')
client = pymongo.MongoClient(f"mongodb+srv://{DBUSERNAME}:{DBPASS}@bonsai.ipxq2.mongodb.net/")
db = client['bonsai']
tree_col = db['trees']
parts_col = db['parts']

class Tree():

    def __init__(self, base, trunk, leaf_pattern):
        self.base = base
        self.trunk = trunk
        self.leaf_pattern = leaf_pattern
    
class User():
    def __init__(self, user_id, tree_1, tree_2, tree_3, balance=1000, inventory={'bases' : [], 'trunks' : [], 'leaf_patterns' : []}):
        self.user_id = user_id
        self.tree_1 = tree_1
        self.tree_2 = tree_2
        self.tree_3 = tree_3
        self.balance = balance
        self.inventory = inventory

def create_tree_image(user, tree_num):
    # save with BytesIO and then paste to image
    base_image = Image.open(BytesIO(user[f'tree_{tree_num}']['base']))
    trunk_image = Image.open(BytesIO(user[f'tree_{tree_num}']['trunk']))
    leaf_pattern_image = Image.open(BytesIO(user[f'tree_{tree_num}']['leaf_pattern']))
    tree_image = Image.new("RGB", (15, 15), (0, 0, 255))
    tree_image.paste(base_image, (0, 12), base_image)
    tree_image.paste(trunk_image, mask=trunk_image)
    tree_image.paste(leaf_pattern_image, mask=leaf_pattern_image)
    
    # resize tree so user can see it
    tree_image = tree_image.resize((tree_image.size[0] * 10, tree_image.size[1] * 10), resample=Image.NEAREST)

    # save with BytesIO to send as embed in discord
    with BytesIO() as image_binary:
        tree_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        im_tree = discord.File(fp=image_binary, filename='image.png')
        return im_tree

def binary_to_embed(binary):
    part_image = Image.open(BytesIO(binary))
    part_image = part_image.resize((part_image.size[0] * 10, part_image.size[1] * 10), Image.NEAREST)

    with BytesIO() as image_binary:
        part_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        im_part = discord.File(fp=image_binary, filename='image.png')
        return im_part

async def check_attachment(ctx, width, height):
    # check for attachment
    if len(ctx.message.attachments) == 0:
        await ctx.send("Attach a file ending with jpg, jpeg, or png.")
        return False
    
    # check for correct extension
    pic_ext = ['.jpg', '.jpeg', '.png']
    match = False
    for ext in pic_ext:
        if ctx.message.attachments[0].filename.endswith(ext):
            match = True
    
    if match == False:
        await ctx.send("The file must end with jpg, jpeg, or png.")
        return False

    # check for correct size
    if not ctx.message.attachments[0].width == width or not ctx.message.attachments[0].height == height:
        await ctx.send(f'Wrong size ({ctx.message.attachments[0].width} x {ctx.message.attachments[0].height})! The base must be {width} x {height}.')
        return False

# create default tree
default_base = None
with open("default_base.png", "rb") as imageFile:
    default_base = imageFile.read()

default_trunk = None
with open("default_trunk.png", "rb") as imageFile:
    default_trunk = imageFile.read()

default_leaf_pattern = None
with open("default_leaf_pattern.png", "rb") as imageFile:
    default_leaf_pattern = imageFile.read()

default_tree = Tree(default_base, default_trunk, default_leaf_pattern)

code_matchings = {'base' : 'bases', 'trunk' : 'trunks', 'leafpattern' : 'leaf_patterns'}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='reset')
async def reset_tree(ctx, tree_num : int):

    # check for valid tree
    if tree_num < 1 or tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_tree.__dict__, default_tree.__dict__, default_tree.__dict__).__dict__
        tree_col.insert_one(user)

    # Reset tree and update in db
    user[f'tree_{tree_num}'] = default_tree.__dict__
    tree_col.update_one({'user_id' : ctx.author.id}, {"$set" : user})

    im_tree = create_tree_image(user, tree_num)
    
    embed = discord.Embed(title='Tree', color=25600)\
        .set_author(name=ctx.author.name)\
        .set_image(url='attachment://image.png')
    
    await ctx.send(file=im_tree, embed=embed)

@bot.command(name='tree')
async def display_tree(ctx, tree_num : int):

    if tree_num < 1 or tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_tree.__dict__, default_tree.__dict__, default_tree.__dict__).__dict__
        tree_col.insert_one(user)

    im_tree = create_tree_image(user, tree_num)

    embed = discord.Embed(title=f'Tree {tree_num}', color=25600)\
        .set_author(name=ctx.author.name)\
        .set_image(url='attachment://image.png')

    await ctx.send(file=im_tree, embed=embed)
    
@bot.command(name="list")
async def upload(ctx, part_type, part_name, list_price : int):
    
    if part_type not in ['base', 'trunk', 'leafpattern']:
        await ctx.send("Enter base, trunk, or leafpattern.")
        return
        
    if list_price < 0:
        await ctx.send("List price cannot be less than 0.")
        return
    
    if part_type == 'base':
        if await check_attachment(ctx, 15, 3) == False:
            return

    elif part_type in ['trunk', 'leafpattern']:
        if await check_attachment(ctx, 15, 12) == False:
            return

    user = parts_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = {'user_id' : ctx.author.id, 'bases' : [], 'trunks' : [], 'leaf_patterns' : []}
        parts_col.insert_one(user)

    code_part_type = code_matchings[part_type]

    parts = user[code_part_type]
    if len(parts) >= 3:
        await ctx.send(f"You have exceeded your limit of 3 on {part_type}s.")
        return

    for part in parts:
        if part['name'].lower() == part_name.lower():
            await ctx.send(f"You have already listed a {part_type} with the name {parts['name']}.")
            return

    attachment_url = ctx.message.attachments[0].url
    file_request = requests.get(attachment_url)
    parts.append({'image' : file_request.content, 'name' : part_name, 'price' : list_price})

    parts_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    im_trunk = binary_to_embed(file_request.content)

    embed = discord.Embed(title=f'New {part_type} Listing', color=255)\
        .set_author(name= ctx.author.name)\
        .add_field(name='Name', value=part_name)\
        .add_field(name='List Price', value=list_price)\
        .set_image(url='attachment://image.png')

    await ctx.send(file=im_trunk, embed=embed)

@bot.command(name="shop")
async def shop_parts(ctx, part_type, member : discord.Member):

    if part_type not in ['base', 'trunk', 'leafpattern']:
        await ctx.send("Enter base, trunk, or leafpattern.")
        return

    seller = parts_col.find_one({'user_id' : member.id})
    
    if seller == None:
        await ctx.send(f"{member} has nothing in their shop.")
        return
    
    i = 0
    code_part_type = code_matchings[part_type]
    parts = seller[code_part_type]
    for part in parts:
        part_picture = binary_to_embed(parts[i]['image'])

        embed = discord.Embed(title=f'{part_type} Listing {i + 1}', color=255)\
            .set_author(name=member.name)\
            .add_field(name='Name', value=part['name'])\
            .add_field(name='List Price', value=part['price'])\
            .set_image(url='attachment://image.png')

        await ctx.send(file=part_picture, embed=embed)

        i += 1

@bot.command(name="buy")
async def buy_part(ctx, part_type, part_name, member : discord.Member):

    if part_type not in ['base', 'trunk', 'leafpattern']:
        await ctx.send("Enter base, trunk, or leafpattern.")
        return
    
    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_tree.__dict__, default_tree.__dict__, default_tree.__dict__).__dict__
        tree_col.insert_one(user)

    seller = parts_col.find_one({'user_id' : member.id})
    
    if seller == None:
        await ctx.send(f"{member} has nothing in their shop.")
        return

    # get correct spelling of list in seller
    code_part_type = code_matchings[part_type]

    parts = seller[code_part_type]
    part_to_buy = None

    for part in parts:
        if part['name'].lower() == part_name.lower():
            part_to_buy = part
    
    if part_to_buy == None:
        await ctx.send(f"{member} doesn't have a {part_type} named {part_name}.")
        return
    
    if part_to_buy['price'] > user['balance']:
        await ctx.send(f"{ctx.author} only has {user['balance']}, but this costs {part_to_buy['price']}.")
        return
    
    user['inventory'][code_part_type].append(part_to_buy)
    user['balance'] -= part_to_buy['price']
    tree_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    await ctx.send(f"{ctx.author} bought {member}'s {part_type}, {part_to_buy['name']}.")
# never_sleep.awake('https://Bonsai-Discord-Bot.xcloudzx.repl.co', False)
bot.run(TOKEN)