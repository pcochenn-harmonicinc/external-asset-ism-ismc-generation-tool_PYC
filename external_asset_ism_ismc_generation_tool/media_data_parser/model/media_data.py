from typing import List

from external_asset_ism_ismc_generation_tool.common.base_model import BaseModel
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_track_info import MediaTrackInfo


class MediaData(BaseModel):
    _media_duration: int = 0
    _media_track_info_list: List[MediaTrackInfo] = []
    
    def __init__(self, media_duration: int, media_track_info_list: List[MediaTrackInfo]):
        self._media_duration = media_duration
        self._media_track_info_list = media_track_info_list

    @property
    def media_duration(self) -> int:
        return self._media_duration

    @media_duration.setter
    def media_duration(self, value: int):
        self._media_duration = value

    @property
    def media_track_info_list(self) -> List[MediaTrackInfo]:
        return self._media_track_info_list

    @media_track_info_list.setter
    def media_track_info_list(self, value: List[MediaTrackInfo]):
        self._media_track_info_list = value

    def __iadd__(self, other):
        if isinstance(other, list):
            self._media_track_info_list.extend(other)
        return self
