import discord
from discord.ext import commands
from PIL import Image
from asyncio import TimeoutError

from utils.default import valid_parts, user_col
from utils.find import find_or_insert_user
from utils.image import bytes_to_file
from utils.embeds import shop_part_embed, error_embed, info_embed
from utils.checks import check_attachment

class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="list")
    async def create_part_listing(self, ctx, part_type, part_name, list_price : int):
        """List a part on the player's shop."""

        part_type = part_type.lower()
        if part_type not in valid_parts:
            await ctx.send(embed=error_embed(ctx.author, "Enter base, trunk, or leaves."))
            return
        
        if len(part_name) > 50:
            await ctx.send(embed=error_embed(ctx.author, "Part Name cannot be over 50 characters long."))
            return
        
        if list_price < 0 or list_price > 10000:
            await ctx.send(embed=error_embed(ctx.author, "List Price cannot be less than $0 or over $10,000."))
            return
        
        if part_type == "base" and await check_attachment(ctx, 15, 3) == False:
            return

        elif part_type in ["trunk", "leaves"] and await check_attachment(ctx, 15, 12) == False:
            return

        user = find_or_insert_user(ctx.author.id)

        parts = user["parts"]

        if len(parts) >= 15:
            await ctx.send(embed=error_embed(ctx.author, "You have exceeded the limit of 15 parts."))
            return

        for part in parts:
            if part["name"].lower() == part_name.lower():
                await ctx.send(embed=error_embed(ctx.author, f"You have already listed a part with the name {part['name']}."))
                return

        # get image file with aiohttp
        attachment_bytes = await ctx.message.attachments[0].read()
        
        parts.append({"image" : attachment_bytes, "name" : part_name, "type" : part_type, "price" : list_price})

        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        im_part = bytes_to_file(attachment_bytes)

        embed = discord.Embed(title=f"New {part_type} Listing", color=255)\
            .set_author(name= str(ctx.author))\
            .add_field(name="Name", value=part_name)\
            .add_field(name="List Price", value=list_price)\
            .set_image(url="attachment://image.png")

        await ctx.send(file=im_part, embed=embed)

    @commands.command("unlist")
    async def delete_part_listing(self, ctx, part_name):
        """Delete a listing from the player's shop."""

        user = find_or_insert_user(ctx.author.id)
        
        part_for_removal = None
        for i, part in enumerate(user["parts"]):
            if part["name"].lower() == part_name.lower():
                part_for_removal = part["name"]
                break
        
        if part_for_removal == None:
            await ctx.send(embed=error_embed(ctx.author, f"Part {part_name} was not found."))
            return
        
        user["parts"].pop(i)
        user_col.update_one({"user_id" : ctx.author.id}, {"$set" : user})

        await ctx.send(embed=info_embed(ctx.author, f"Unlisted part {part_for_removal}."))
        
    @commands.command(name="shop")
    async def shop_parts(self, ctx, part_type, member : discord.User = None):
        """View all the parts in a player's shop."""

        part_type = part_type.lower()
        if part_type not in valid_parts:
            await ctx.send(embed=error_embed(ctx.author, "Enter base, trunk, or leaves."))
            return

        if member == None:
            member = ctx.author
        
        seller = user_col.find_one({"user_id" : member.id})
        
        if seller == None:
            await ctx.send(embed=error_embed(ctx.author, f"{member} has no parts listed."))
            return
            
        all_parts = seller["parts"]
        
        parts = []
        for part in all_parts:
            if part["type"] == part_type:
                parts.append(part)
        
        if len(parts) == 0:
            await ctx.send(embed=error_embed(ctx.author, f"{member} has no parts of that type listed."))
            return

        part_picture = bytes_to_file(parts[0]["image"])

        total_parts = len(parts)

        embed = shop_part_embed(member, parts, 1, total_parts)
        
        shop_message = await ctx.send(file=part_picture, embed=embed)

        if len(parts) == 1:
            return
        
        await shop_message.add_reaction("⬅️")
        await shop_message.add_reaction("➡️")

        def check(reaction, user):
            return reaction.message.id == shop_message.id and user.id == ctx.author.id and str(reaction.emoji) in ["⬅️", "➡️"]

        current_part = 1

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)

                # check for arrow reactions
                if str(reaction.emoji) == "⬅️" and current_part > 1:
                    current_part -= 1
                    
                    part_picture = bytes_to_file(parts[current_part-1]["image"])

                    embed = shop_part_embed(member, parts, current_part, total_parts)
                    
                    await shop_message.delete()
                    shop_message = await ctx.send(file=part_picture, embed=embed)
                    await shop_message.add_reaction("⬅️")
                    await shop_message.add_reaction("➡️")

                elif str(reaction.emoji) == "➡️" and current_part < total_parts:
                    
                    current_part += 1

                    part_picture = bytes_to_file(parts[current_part-1]["image"])

                    embed = shop_part_embed(member, parts, current_part, total_parts)

                    await shop_message.delete()
                    shop_message = await ctx.send(file=part_picture, embed=embed)
                    await shop_message.add_reaction("⬅️")
                    await shop_message.add_reaction("➡️")

            except TimeoutError:
                await shop_message.clear_reaction("⬅️")
                await shop_message.clear_reaction("➡️")
                break
    
    @commands.command(name="shoprandom")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def shop_random_parts(self, ctx):
        """View a random part from a player's shop."""

        user = None

        # run up to 50 times
        for _ in range(50):
            # get users 5 at a time
            users = user_col.aggregate([{"$sample" : {"size" : 5}}])
            
            # if user has a part, break
            for possible_user in users:
                if len(possible_user["parts"]) > 0:
                    user = possible_user
                    break
        
        parts = user["parts"]

        part_picture = bytes_to_file(parts[0]["image"])

        total_parts = len(parts)

        username = str(await self.bot.fetch_user(user["user_id"]))

        embed = shop_part_embed(username, parts, 1, total_parts)
        
        shop_message = await ctx.send(file=part_picture, embed=embed)

        if len(parts) == 1:
            return
        
        await shop_message.add_reaction("⬅️")
        await shop_message.add_reaction("➡️")

        def check(reaction, user):
            return reaction.message.id == shop_message.id and user.id == ctx.author.id and str(reaction.emoji) in ["⬅️", "➡️"]

        current_part = 1

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)

                # check for arrow reactions
                if str(reaction.emoji) == "⬅️" and current_part > 1:
                    current_part -= 1
                    
                    part_picture = bytes_to_file(parts[current_part-1]["image"])

                    embed = shop_part_embed(username, parts, current_part, total_parts)
                    
                    await shop_message.delete()
                    shop_message = await ctx.send(file=part_picture, embed=embed)
                    await shop_message.add_reaction("⬅️")
                    await shop_message.add_reaction("➡️")

                elif str(reaction.emoji) == "➡️" and current_part < total_parts:
                    
                    current_part += 1

                    part_picture = bytes_to_file(parts[current_part-1]["image"])

                    embed = shop_part_embed(username, parts, current_part, total_parts)

                    await shop_message.delete()
                    shop_message = await ctx.send(file=part_picture, embed=embed)
                    await shop_message.add_reaction("⬅️")
                    await shop_message.add_reaction("➡️")

            except TimeoutError:
                await shop_message.clear_reaction("⬅️")
                await shop_message.clear_reaction("➡️")
                break
        


    @commands.command(name="buy")
    async def buy_part(self, ctx, part_name, member : discord.User = None):
        """Buy a part from a player's shop."""

        user = find_or_insert_user(ctx.author.id)

        if len(user["inventory"]) >= 100:
            await ctx.send(embed=error_embed(ctx.author, "You have reached the limit of 100 parts in your inventory."))
            return
        
        if member == None:
            member = ctx.author
        
        seller = user_col.find_one({"user_id" : member.id})

        if seller == None:
            await ctx.send(embed=error_embed(ctx.author, f"{member} has no parts listed."))
            return

        # get correct spelling of list in seller
        all_parts = seller["parts"]
        part_to_buy = None

        for part in all_parts:
            if part["name"].lower() == part_name.lower():
                part_to_buy = part
        
        if part_to_buy == None:
            await ctx.send(embed=error_embed(ctx.author, f"{member} does not have a part named {part_name}."))
            return
        
        if part_to_buy["price"] > user["balance"]:
            await ctx.send(embed=error_embed(ctx.author, f"You only have ${user['balance']}, but {part_to_buy['name']} costs ${part_to_buy['price']}."))
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

        await ctx.send(embed=info_embed(ctx.author, f"You bought {member}'s {part_to_buy['name']}."))

def setup(bot):
    bot.add_cog(Shop(bot))
