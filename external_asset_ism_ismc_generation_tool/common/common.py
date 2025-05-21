import json
import os
from typing import Optional, Tuple, Union, List
import pycountry

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_format import MediaFormat
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_track_info import MediaTrackInfo
from external_asset_ism_ismc_generation_tool.media_data_parser.model.track_type import TrackType

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger


class Common:
    __logger: ILogger = Logger("Common")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def read_json(json_path):
        with open(os.path.basename(json_path), 'r') as json_f:
            return json.load(json_f)

    @staticmethod
    def is_file_exists(path):
        return os.path.isfile(path)

    @staticmethod
    def sort_attributes_in_xml(root):
        for el in root.iter():
            attrib = el.attrib
            if len(attrib) > 1:
                attributes = sorted(attrib.items())
                attrib.clear()
                attrib.update(attributes)

    @staticmethod
    def merge_dicts(dict_list: list[dict]) -> dict:
        merged_dict: Optional[dict] = None
        for dictionary in dict_list:
            if dictionary is not None:
                merged_dict = dictionary if not merged_dict else {**merged_dict, **dictionary}
        if merged_dict:
            return {key: value for key, value in merged_dict.items() if value is not None}
        else:
            return {}

    @staticmethod
    def get_key_and_format(blob_name) -> Tuple[Optional[str], str]:
        key = None
        split_name = blob_name.rsplit(".", 1)
        format = split_name[1]
        if not MediaFormat.is_mpi_format(blob_name):
            key = split_name[0]
        elif MediaFormat.is_mpi_format(blob_name):
            parts = split_name[0].rsplit("_", 1)
            if parts[1].isdigit():
                key = parts[0]

        return key, format

    @staticmethod
    def get_last_track_id(mp4_track_info: list) -> int:
        return max(track.track_id for track in mp4_track_info) if mp4_track_info else 1

    @staticmethod
    def get_completed_tasks(task_mapping, executor: Union[ThreadPoolExecutor, ProcessPoolExecutor]) -> any:
        return as_completed(task_mapping) if executor else task_mapping

    @staticmethod
    def get_language_3_code_and_name(language_code: str):
        obsolete_language_codes = {
            'scr': 'hrv'  # Mapping 'scr' to 'hrv' for Croatian as 'scr' is obsolete now
            }

        if language_code in obsolete_language_codes:
            language_code = obsolete_language_codes[language_code]

        language_info = pycountry.languages.lookup(language_code)
        if language_info:
            return language_info.alpha_3, language_info.name
        else:
            return language_code, language_code

    @staticmethod
    def get_filtered_tracks(media_track_infos: List[MediaTrackInfo], track_type: TrackType) -> List[MediaTrackInfo]:
        return [track for track in media_track_infos if track.track_type == track_type]

    @staticmethod
    def group_tracks_by_quality(tracks: List[MediaTrackInfo]) -> List[MediaTrackInfo]:
        different_tracks = []
        for track in tracks:
            if not (different_tracks and track.is_equal_language(different_tracks[-1]) and track.is_equal_bitrate(different_tracks[-1])):
                different_tracks.append(track)
        return different_tracks
