from enum import Enum

class PermissionLevel(Enum):
    ANYONE = 0
    MEMBER = 1
    MOD = 2
    ADMIN = 3
    DEV = 4