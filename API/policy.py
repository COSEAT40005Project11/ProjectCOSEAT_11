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
    "reviewer": {"knowledge:read","knowledge:decide"},
    "custodian": {"knowledge:read","knowledge:decide","knowledge:submit", "consent:manage"},
    "admin": {"knowledge:read", "knowledge:submit","knowledge:delete", "consent:manage","knowledge:decide","users:manage"}
}







def can_view(user: dict, level: str) -> bool:
    clearance = CLEARANCE.get(user.get("role"))
    if clearance is None or level not in LEVELS:
        return False
    return LEVELS.index(level) <= LEVELS.index(clearance)

def can_decide(user: dict, level: str) -> bool:
    return has_permission(user, "knowledge:decide") and can_view(user, level)

def has_permission(user: dict, permission: str) -> bool:
    return permission in PERMISSIONS.get(user.get("role"), set())

def ask_level(user: dict) -> str:
    clearance = CLEARANCE.get(user.get("role"), "public")
    return "restricted" if clearance == "sacred" else clearance