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
base_col = db['bases']
trunk_col = db['trunks']
leaf_pattern_col = db['leaf_patterns']

class Tree():

    def __init__(self, base, trunk, leaf_pattern):
        self.base = base
        self.trunk = trunk
        self.leaf_pattern = leaf_pattern
    
class User():
    def __init__(self, user_id, tree_1, tree_2, tree_3):
        self.user_id = user_id
        self.tree_1 = tree_1
        self.tree_2 = tree_2
        self.tree_3 = tree_3

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

# create default tree
default_base = 0
with open("default_base.png", "rb") as imageFile:
    default_base = imageFile.read()

default_trunk = 0
with open("default_trunk.png", "rb") as imageFile:
    default_trunk = imageFile.read()

default_leaf_pattern = 0
with open("default_leaf_pattern.png", "rb") as imageFile:
    default_leaf_pattern = imageFile.read()

default_tree = Tree(default_base, default_trunk, default_leaf_pattern)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='reset')
async def reset_tree(ctx, tree_num : int):

    # check for valid tree
    if tree_num < 1 or tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    user = 0
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

    user = 0
    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_tree.__dict__, default_tree.__dict__, default_tree.__dict__).__dict__
        tree_col.insert_one(user)

    im_tree = create_tree_image(user, tree_num)

    embed = discord.Embed(title=f'Tree {tree_num}', color=25600)\
        .set_author(name=ctx.author.name)\
        .set_image(url='attachment://image.png')

    await ctx.send(file=im_tree, embed=embed)

# never_sleep.awake('https://Bonsai-Discord-Bot.xcloudzx.repl.co', False)
bot.run(TOKEN)