def defaults():
    """Create default_tree, default_user, and list of valid parts."""
    
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

    return (default_tree, default_user, valid_parts)