import discord

from PIL import Image
from io import BytesIO

def create_tree_image(user, tree_to_display):
    """Turn byte data into an image."""
    
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

def binary_to_file(binary):
    """Turn binary into a discord.File."""

    part_image = Image.open(BytesIO(binary))
    part_image = part_image.resize((part_image.size[0] * 10, part_image.size[1] * 10), Image.NEAREST)

    with BytesIO() as image_binary:
        part_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        im_part = discord.File(fp=image_binary, filename='image.png')
        return im_part