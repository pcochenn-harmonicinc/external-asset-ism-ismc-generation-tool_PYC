from enum import Enum
from typing import List

class MediaFormat(Enum):
    MP4 = "mp4"
    MPI = "mpi"
    ISMV = "ismv"
    ISMA = "isma"
    TTML = "ttml"
    VTT = "vtt"
    CMFT = "cmft"

    UNKNOWN = None

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN

    @classmethod
    def is_media_format(cls, name: str) -> bool:
        return cls._ends_with_any(name, [
            cls.MP4.value,
            cls.MPI.value,
            cls.ISMV.value,
            cls.ISMA.value,
            cls.CMFT.value
        ])

    @classmethod
    def is_text_format(cls, name: str) -> bool:
        return cls._ends_with_any(name, [
            cls.VTT.value,
            cls.TTML.value
        ])

    @classmethod
    def is_mpi_format(cls, name: str) -> bool:
        return name.lower().endswith(cls.MPI.value)

    @classmethod
    def get_format(cls, name: str) -> str:
        for media_format in cls:
            if media_format is not cls.UNKNOWN and media_format.value and name.lower().endswith(media_format.value):
                return media_format.value
        return ""

    @staticmethod
    def _ends_with_any(name: str, suffixes: List[str]) -> bool:
        return any(name.lower().endswith(suffix) for suffix in suffixes)