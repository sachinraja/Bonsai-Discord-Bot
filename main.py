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
from random import randint
import asyncio
from math import ceil
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

# remove help command to add custom one
bot.remove_command('help')

# mongodb
client = pymongo.MongoClient(f"mongodb+srv://{DBUSERNAME}:{DBPASS}@bonsai.ipxq2.mongodb.net/")
db = client['bonsai']
tree_col = db['trees']
parts_col = db['parts']

# starter classes for storing
class Tree():

    def __init__(self, base, trunk, leaf_pattern, background_color=(0, 0, 255)):
        self.base = base
        self.trunk = trunk
        self.leaf_pattern = leaf_pattern
        self.background_color = background_color
    
class User():
    def __init__(self, user_id, trees, balance=200, inventory=[]):
        self.user_id = user_id
        self.trees = trees
        self.balance = balance
        self.inventory = inventory

def create_tree_image(user, tree_num):
    # save with BytesIO and then paste to image
    base_image = Image.open(BytesIO(user['trees'][tree_num]['base']['part_info']['image']))
    trunk_image = Image.open(BytesIO(user['trees'][tree_num]['trunk']['part_info']['image']))
    leaf_pattern_image = Image.open(BytesIO(user['trees'][tree_num]['leaf_pattern']['part_info']['image']))
    tree_image = Image.new("RGB", (15, 15), tuple(user['trees'][tree_num]['background_color']))
    tree_image.paste(base_image, (0, 12), mask=base_image)
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

def create_tree_embed(user, author_name, input_tree_num, tree_num):
    embed = discord.Embed(title=f'Tree {input_tree_num}', color=25600)\
        .set_author(name=author_name)\
        .add_field(name='Base', value=f"{user['trees'][tree_num]['base']['creator']}'s {user['trees'][tree_num]['base']['part_info']['name']}")\
        .add_field(name='Trunk', value=f"{user['trees'][tree_num]['trunk']['creator']}'s {user['trees'][tree_num]['trunk']['part_info']['name']}")\
        .add_field(name='Leaf Pattern', value=f"{user['trees'][tree_num]['leaf_pattern']['creator']}'s {user['trees'][tree_num]['leaf_pattern']['part_info']['name']}")\
        .set_image(url='attachment://image.png')

    return embed

async def check_attachment(ctx, width, height):
    # check for attachment on message
    if len(ctx.message.attachments) == 0:
        await ctx.send("Attach a file ending with jpg, jpeg, or png.")
        return False
    
    # check for correct extension on attachment
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

default_tree = Tree({'part_info' : {'image' : default_base, 'name' : 'Default Base', 'type' : 'base', 'price' : 0}, 'creator' : 'Default'}, {'part_info' : {'image' : default_trunk, 'name' : 'Default Trunk', 'type' : 'trunk', 'price' : 0}, 'creator' : 'Default'}, {'part_info' : {'image' : default_leaf_pattern, 'name' : 'Default Leaf Pattern', 'type' : 'leafpattern', 'price' : 0}, 'creator' : 'Default'})
default_trees = (default_tree.__dict__, default_tree.__dict__, default_tree.__dict__)

valid_parts = ('base', 'trunk', 'leafpattern')
code_matchings = {'base' : 'base', 'trunk' : 'trunk', 'leafpattern' : 'leaf_pattern'}

@bot.event
async def on_ready():
    
    print(f'Logged in as {bot.user.name}')

@bot.command(name='help')
async def help(ctx):

    embed = discord.Embed(title='Help', color=65280)\
        .add_field(name="Argument Meanings", value="Part Type : base, trunk, or leafpattern.\nMember=optional : If you don't input a member here, it will default to yourself.")\
        .add_field(name="b!balance [Member=optional]", value="Shows your balance or the balance of someone else.", inline=False)\
        .add_field(name="b!buy [Part Name] [Member]", value="Buy a part from a member.", inline=False)\
        .add_field(name="b!daily", value="Claim your daily reward ($50-$100).", inline=False)\
        .add_field(name="b!help", value="Displays this message.", inline=False)\
        .add_field(name="b!inventory [Member=optional]", value="Displays all the parts in your inventory and their corresponding inventory number.", inline=False)\
        .add_field(name="b!list [Part Type] [Part Name <= 20] [List Price > 0]", value="List a part for sale. This must have an attached image to use for the part. Bases must be 15 x 3. Trunks must be 15 x 12. Leaf Patterns must be 15 x 12.", inline=False)\
        .add_field(name="b!replace [1 <= Tree Number >= 3] [Inventory Number]", value="Replace a part on a tree with one in your inventory.", inline=False)\
        .add_field(name="b!replacecolor [1 <= Tree Number >= 3] [Color Hex Code]", value="Replace the background color of a tree.", inline=False)\
        .add_field(name="b!reset [1 <= Tree Number >= 3]", value="Reset a tree to defaults.", inline=False)\
        .add_field(name="b!shop [Part Type] [Member=optional]", value="Show all the parts that Member has listed as Part Type.", inline=False)\
        .add_field(name="b!tree [1 <= Tree Number >= 3]", value="Displays the tree.", inline=False)
        
    await ctx.send(embed=embed)

@bot.command(name='tree')
async def display_tree(ctx, input_tree_num : int):

    if input_tree_num < 1 or input_tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    tree_num = input_tree_num - 1

    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_trees).__dict__
        tree_col.insert_one(user)

    im_tree = create_tree_image(user, tree_num)
    embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)

    await ctx.send(file=im_tree, embed=embed)

@bot.command(name='reset')
async def reset_tree(ctx, input_tree_num : int):

    # check for valid tree
    if input_tree_num < 1 or input_tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    tree_num = input_tree_num - 1

    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_trees).__dict__
        tree_col.insert_one(user)

    # Reset tree and update in db
    user['trees'][tree_num] = default_tree.__dict__
    tree_col.update_one({'user_id' : ctx.author.id}, {"$set" : user})

    im_tree = create_tree_image(user, tree_num)
    embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)
    
    await ctx.send(file=im_tree, embed=embed)

@bot.command(name="list")
async def upload(ctx, part_type, part_name, list_price : int):
    
    if part_type not in valid_parts:
        await ctx.send("Enter base, trunk, or leafpattern.")
        return
    
    if len(part_name) > 20:
        await ctx.send("Part Name cannot be over 20 characters long.")
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
        user = {'user_id' : ctx.author.id, 'parts' : []}
        parts_col.insert_one(user)

    # prepare for future where they can gain money
    if tree_col.find_one({'user_id' : ctx.author.id}) == None:
        tree_col.insert_one(User(ctx.author.id, default_trees).__dict__)

    parts = user['parts']

    if len(parts) >= 10:
        await ctx.send(f"You have exceeded your limit of 10 parts.")
        return

    for part in parts:
        if part['name'].lower() == part_name.lower():
            await ctx.send(f"You have already listed a part with the name {part['name']}.")
            return

    attachment_url = ctx.message.attachments[0].url
    file_request = requests.get(attachment_url)
    parts.append({'image' : file_request.content, 'name' : part_name, 'type' : part_type, 'price' : list_price})

    parts_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    im_part = binary_to_embed(file_request.content)

    embed = discord.Embed(title=f'New {part_type} Listing', color=255)\
        .set_author(name= ctx.author.name)\
        .add_field(name='Name', value=part_name)\
        .add_field(name='List Price', value=list_price)\
        .set_image(url='attachment://image.png')

    await ctx.send(file=im_part, embed=embed)

@bot.command(name="shop")
async def shop_parts(ctx, part_type, member : discord.Member = None):
    
    if part_type not in valid_parts:
        await ctx.send("Enter base, trunk, or leafpattern.")
        return

    if member == None:
        member = ctx.author
    
    seller = parts_col.find_one({'user_id' : member.id})
    
    if seller == None:
        await ctx.send(f"{member} has nothing in their shop.")
        return
        
    all_parts = seller['parts']
    
    parts = []
    for p in all_parts:
        if p['type'] == part_type:
            parts.append(p)
    
    if parts == []:
        await ctx.send(f"{seller} has no {part_type}s.")
        return

    part_picture = binary_to_embed(parts[0]['image'])

    embed = discord.Embed(title=f"{parts[0]['type']} Listing 1", color=255)\
        .set_author(name=member.name)\
        .add_field(name='Name', value=parts[0]['name'])\
        .add_field(name='List Price', value=parts[0]['price'])\
        .set_image(url='attachment://image.png')

    shop_message = await ctx.send(file=part_picture, embed=embed)

    await shop_message.add_reaction('⬅️')
    await shop_message.add_reaction('➡️')

    def check(reaction, user):
        return reaction.message.id == shop_message.id and user.id == ctx.author.id and str(reaction.emoji) in ['⬅️', '➡️']

    total_parts = len(parts) - 1
    current_part = 0

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=300)

            # check for arrow reactions
            if str(reaction.emoji) == '⬅️' and current_part != 0:
                current_part -= 1

                part_picture = binary_to_embed(parts[current_part]['image'])

                embed = discord.Embed(title=f"{parts[current_part]['type']} Listing {current_part + 1}", color=255)\
                    .set_author(name=member.name)\
                    .add_field(name='Name', value=parts[current_part]['name'])\
                    .add_field(name='List Price', value=parts[current_part]['price'])\
                    .set_image(url='attachment://image.png')

                await shop_message.edit(embed=embed)
                await shop_message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == '➡️' and current_part != total_parts:
                current_part += 1

                part_picture = binary_to_embed(parts[current_part]['image'])

                embed = discord.Embed(title=f"{parts[current_part]['type']} Listing {current_part + 1}", color=255)\
                    .set_author(name=member.name)\
                    .add_field(name='Name', value=parts[current_part]['name'])\
                    .add_field(name='List Price', value=parts[current_part]['price'])\
                    .set_image(url='attachment://image.png')

                await shop_message.edit(embed=embed)
                await shop_message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            break
    
@bot.command(name="buy")
async def buy_part(ctx, part_name, member : discord.Member):
    
    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_trees).__dict__
        tree_col.insert_one(user)

    seller = parts_col.find_one({'user_id' : member.id})

    if seller == None:
        await ctx.send(f"{member} has nothing in their shop.")
        return

    # get correct spelling of list in seller
    all_parts = seller['parts']
    part_to_buy = None

    for part in all_parts:
        if part['name'].lower() == part_name.lower():
            part_to_buy = part
    
    if part_to_buy == None:
        await ctx.send(f"{member} doesn't have a part named {part_name}.")
        return
    
    if part_to_buy['price'] > user['balance']:
        await ctx.send(f"You only have ${user['balance']}, but {part_to_buy['name']} costs ${part_to_buy['price']}.")
        return
    
    # give part and remove money from user
    user['inventory'].append({'part_info' : part_to_buy, 'creator' : str(member)})
    user['balance'] -= part_to_buy['price']
    tree_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    # give money to seller
    seller_tree_account = tree_col.find_one({'user_id' : member.id})
    seller_tree_account['balance'] += part_to_buy['price']
    tree_col.update_one({'user_id' : member.id}, {'$set' : seller_tree_account})

    await ctx.send(f"You bought {member}'s {part_to_buy['name']}.")

@bot.command(name="inventory")
async def list_inventory(ctx, member : discord.Member = None):

    if member == None:
        member = ctx.author
    
    user = tree_col.find_one({'user_id' : member.id})

    embed = discord.Embed(title=f"{member}'s Inventory", color=255)
    
    i = 1
    for part in user['inventory'][:26]:
        embed = embed.add_field(name=part['part_info']['type'], value=f"{i} : {part['creator']}'s {part['part_info']['name']}", inline=False)

        i += 1

    inventory_message = await ctx.send(embed=embed)

    await inventory_message.add_reaction('⬅️')
    await inventory_message.add_reaction('➡️')

    def check(reaction, user):
        return reaction.message.id == inventory_message.id and user.id == ctx.author.id and str(reaction.emoji) in ['⬅️', '➡️']

    total_part_lists = ceil(len(user['inventory']) / 25)
    current_part_list = 1

    while True:
        try:
            reaction, reaction_user = await bot.wait_for('reaction_add', check=check, timeout=300)

            # check for arrow reactions
            if str(reaction.emoji) == '⬅️' and current_part_list > 1:
                current_part_list -= 1

                inventory_index_first = (current_part_list - 1) * 25;
                inventory_index_last = (current_part_list * 25) + 1;

                embed = discord.Embed(title=f"{member}'s Inventory Page {current_part_list}", color=255)
                
                j = inventory_index_first
                for part in user['inventory'][inventory_index_first:inventory_index_last]:
                    embed = embed.add_field(name=part['part_info']['type'], value=f"{j+1} : {part['creator']}'s {part['part_info']['name']}", inline=False)
                    j += 1

                await inventory_message.edit(embed=embed)
                await inventory_message.remove_reaction(reaction, reaction_user)

            elif str(reaction.emoji) == '➡️' and current_part_list < total_part_lists:
                current_part_list += 1

                inventory_index_first = (current_part_list - 1) * 25;
                inventory_index_last = (current_part_list * 25) + 1;
                print(inventory_index_first, inventory_index_last)
                
                embed = discord.Embed(title=f"{member}'s Inventory Page {current_part_list}", color=255)
                
                j = inventory_index_first
                for part in user['inventory'][inventory_index_first:inventory_index_last]:
                    embed = embed.add_field(name=part['part_info']['type'], value=f"{j+1} : {part['creator']}'s {part['part_info']['name']}", inline=False)
                    j += 1

                await inventory_message.edit(embed=embed)
                await inventory_message.remove_reaction(reaction, reaction_user)

        except asyncio.TimeoutError:
            break

@bot.command(name="replace")
async def replace_part(ctx, input_tree_num : int, input_inventory_num : int):
    if input_tree_num < 1 or input_tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    tree_num = input_tree_num - 1

    user = tree_col.find_one({'user_id' : ctx.author.id})
    
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
    
    # get new part from user
    part = user['inventory'].pop(inventory_num)
    
    # set tree part to new part
    part_type = code_matchings[part['part_info']['type']]
    user['trees'][tree_num][part_type] = part

    tree_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    im_tree = create_tree_image(user, tree_num)
    embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)

    await ctx.send(file=im_tree, embed=embed)

@bot.command(name="replacecolor")
async def replace_color(ctx, input_tree_num : int, hex_code):
    
    if input_tree_num < 1 or input_tree_num > 3:
        await ctx.send('Enter a number from 1 to 3.')
        return

    tree_num = input_tree_num - 1

    if len(hex_code) != 7:
        await ctx.send('Enter a valid hex code. Ex: #0000FF.')
        return
    
    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_trees).__dict__
        tree_col.insert_one(user)
    
    # convert to rgb
    try:
        h = hex_code.lstrip('#')
        user['trees'][tree_num]['background_color'] = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    except:
        await ctx.send(f"{hex_code} is not valid.")
        return
    
    tree_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    im_tree = create_tree_image(user, tree_num)
    embed = create_tree_embed(user, ctx.author.name, input_tree_num, tree_num)
    
    await ctx.send(file=im_tree, embed=embed)

@bot.command(name="daily")
@commands.cooldown(1, 60*60*24, commands.BucketType.user)
async def daily_reward(ctx):

    user = tree_col.find_one({'user_id' : ctx.author.id})
    
    if user == None:
        user = User(ctx.author.id, default_trees).__dict__
        tree_col.insert_one(user)
    
    reward = randint(50, 100)
    user['balance'] += randint(50, 100)

    tree_col.update_one({'user_id' : ctx.author.id}, {'$set' : user})

    await ctx.send(f"Added ${reward} to your balance! You now have ${user['balance']}.")

@daily_reward.error
async def daily_reward_error(ctx, error):
    # error message if the command is on cooldown still
    if isinstance(error, commands.CommandOnCooldown):
        # time left on cooldown converted from seconds to hours
        await ctx.send(f'This command is on cooldown, try again in{error.retry_after / 3600: .1f} hours.')

@bot.command(name="balance")
async def check_balance(ctx, member : discord.Member = None):

    if member == None:
        member = ctx.author

    user = tree_col.find_one({'user_id' : member.id})
    
    if user == None:
        user = User(ctx.author.id, default_trees).__dict__
        tree_col.insert_one(user)
    
    await ctx.send(f"{member} has ${user['balance']}.")

bot.run(TOKEN)