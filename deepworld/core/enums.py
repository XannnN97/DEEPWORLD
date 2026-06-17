from enum import Enum


class TrackType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    GENERATOR = "generator"
    UNKNOWN = "unknown"


class TransitionType(Enum):
    CUT = "cut"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    KEY = "key"
    UNKNOWN = "unknown"


class EditType(Enum):
    CUT = "cut"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    KEY = "key"
    FROM_BLACK = "from_black"
    TO_BLACK = "to_black"
    UNKNOWN = "unknown"
