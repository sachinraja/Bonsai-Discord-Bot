from utils.embeds import error_embed

async def check_attachment(ctx, width, height):
    """Check for attachment on message."""

    if len(ctx.message.attachments) == 0:
        await ctx.send(embed=error_embed(ctx.author, "Attach an image ending with jpg, jpeg, or png."))
        return False
    
    # check for correct extension on attachment
    pic_ext = [".jpg", ".jpeg", ".png"]
    match = False
    for ext in pic_ext:
        if ctx.message.attachments[0].filename.endswith(ext):
            match = True
    
    if match == False:
        await ctx.send(embed=error_embed(ctx.author, "Attach an image ending with jpg, jpeg, or png."))
        return False

    # check for correct size
    if ctx.message.attachments[0].width != width or ctx.message.attachments[0].height != height:
        await ctx.send(embed=error_embed(ctx.author, f"Wrong size: ({ctx.message.attachments[0].width} x {ctx.message.attachments[0].height})! The image must be {width} x {height}."))
        return False