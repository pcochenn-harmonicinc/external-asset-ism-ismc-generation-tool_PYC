from enum import Enum
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_format import MediaFormat

class SubtitleFourCC(Enum):
    VTT = "WVTT"
    TTML = "TTML"

    UNKNOWN = ""

    @classmethod
    def get_subtitle_fourcc(cls, name: str) -> str:
        for subtitle_format in cls:
            if MediaFormat.get_format(name) == subtitle_format.name.lower():
                return subtitle_format.value
        return cls.UNKNOWN.value
