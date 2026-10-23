LEVELS = ["public", "community", "restricted", "sacred"]
CLEARANCE = {"anonymous": "public", "viewer": "community",
             "reviewer": "restricted", "custodian": "sacred", "admin": "sacred"}

def can_view(user, level):
    return LEVELS.index(level) <= LEVELS.index(CLEARANCE[user["role"]])

def can_decide(user, level):
    return user["role"] in ("reviewer", "custodian", "admin") and can_view(user, level)