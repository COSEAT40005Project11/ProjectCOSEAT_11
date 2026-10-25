LEVELS = ["public", "community", "restricted", "sacred"]


ROLES = ("viewer", "reviewer", "custodian", "admin")


CLEARANCE = {"anonymous": "public", 
             "viewer": "community",
             "reviewer": "restricted", 
             "custodian": "sacred", 
             "admin": "sacred"}

PERMISSIONS = {
    "anonymous": {"knowledge:read"},
    "viewer": {"knowledge:read"},
    "reviewer": {"knowledge:read","Knowlede:review"},
    "custodian": {"knowledge:read","Knowlede:review","knowledge:submit", "consent:manage"},
    "admin": {"knowledge:read", "knowledge:submit","knowledge:delete", "consent:manage","Knowlede:review","knowledge:submit","users:manage"}
}







def can_view(user, level):
    return LEVELS.index(level) <= LEVELS.index(CLEARANCE[user["role"]])

def can_decide(user, level):
    return user["role"] in ("viewer","admin", "reviewer", "custodian", "anonymous") and can_view(user, level)