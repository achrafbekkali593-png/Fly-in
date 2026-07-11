from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    MAGENTA = "magenta"
    CYAN = "cyan"
    GRAY = "gray"
    GREY = "grey"
    WHITE = "white"

class ZoneType(Enum):
    RESTRICTED = "restricted"
    NORMAL = "normal"
    PRIORITY = "priority"
    BLOCKED = "blocked"
