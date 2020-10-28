from utils.default import default_user, user_col

def find_tree(user, input_tree_name):
    """Loop over trees and find one based on the name. Return tree."""

    tree_to_display = None
    tree_name = input_tree_name.lower()

    for tree in user["trees"]:
        if tree["name"].lower() == tree_name:
            tree_to_display = tree
            break
    
    if tree_to_display == None:
        return None
    
    return tree_to_display

def find_tree_index(user, input_tree_name):
    """Loop over trees and find one based on the name. Return tree index."""

    tree_to_display = None
    tree_name = input_tree_name.lower()

    for i, tree in enumerate(user["trees"]):
        if tree["name"].lower() == tree_name:
            tree_to_display = tree
            break
    
    if tree_to_display == None:
        return None
    
    return i

def find_user(user_id):
    """Return user in db or return None."""

    user = user_col.find_one({"user_id" : user_id})

    return user


def find_or_insert_user(user_id):
    """Create user in db if there is none and return user."""

    user = user_col.find_one({"user_id" : user_id})

    if user == None:
        user = default_user.copy()
        user["user_id"] = user_id
        user_col.insert_one(user)

    return user