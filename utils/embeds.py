import discord

def tree_embed(user, author_name, tree_to_display):
    """Create embed for displaying trees."""
        
    return discord.Embed(title=tree_to_display["name"], color=25600)\
        .set_author(name=author_name)\
        .add_field(name="Base", value=f"{tree_to_display['base']['creator']}'s {tree_to_display['base']['name']}")\
        .add_field(name="Trunk", value=f"{tree_to_display['trunk']['creator']}'s {tree_to_display['trunk']['name']}")\
        .add_field(name="Leaves", value=f"{tree_to_display['leaves']['creator']}'s {tree_to_display['leaves']['name']}")\
        .set_image(url="attachment://image.png")

def inventory_part_embed(part, username):
    """Create embed for displaying inventory parts."""

    return discord.Embed(title=f"{part['type']}", color=255)\
            .set_author(name=username)\
            .add_field(name="Name", value=part["name"])\
            .set_image(url="attachment://image.png")

def shop_part_embed(username, parts, current_part, total_parts):
    """Create embed for displaying shop parts."""
    
    part_index = current_part - 1

    return discord.Embed(color=255)\
            .set_author(name=username)\
            .add_field(name="Name", value=parts[part_index]["name"])\
            .add_field(name="List Price", value=parts[part_index]["price"])\
            .set_image(url="attachment://image.png")\
            .set_footer(text=f"Page {current_part} / {total_parts}")

def error_embed(username, error_message):
    """Create embed for error messages."""

    return discord.Embed(color=16711680)\
        .set_author(name=username)\
        .add_field(name="Error", value=error_message)

def info_embed(username, info_message):
    """Create embed for informational (output) messages."""

    return discord.Embed(color=8900331)\
        .set_author(name=username)\
        .add_field(name="Information", value=info_message)