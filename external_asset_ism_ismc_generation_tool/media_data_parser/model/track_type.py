from enum import Enum


class TrackType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    SUBT = "subt"

    UNKNOWN = None

    @classmethod
    def _missing_(cls, value):
        return TrackType.UNKNOWN
