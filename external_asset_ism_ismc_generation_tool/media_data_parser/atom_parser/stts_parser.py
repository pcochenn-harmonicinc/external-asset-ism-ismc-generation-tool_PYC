from typing import Optional, List

from tools.pymp4.src.pymp4.parser import Box

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.model.track_type import TrackType


class STTSParser:
    __logger: ILogger = Logger("STTSParser")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    def __init__(self, stts_atom: Box):
        self.stts_atom = stts_atom
        self.stts_atom_entries = stts_atom['entries']

    def get_sample_count(self) -> int:
        return sum(entry.sample_count for entry in self.stts_atom_entries)

    def aggregate_sample_info(self) -> List:
        sample_info = []
        cumulative = 0
        for entry in self.stts_atom_entries:
            cumulative += entry.sample_count
            sample_info.append((cumulative, entry.sample_delta))
        return sample_info

    def get_chunk_durations_from_stts(self, track_type: TrackType, timescale: int, key_frames_numbers: Optional[list] = None) -> list:
        _SEGMENT_DURATION = 2  # 2 sec TODO: move to general settings
        chunk_durations: list = []

        sample_info_list = self.aggregate_sample_info()
        sample_number = 1
        chunk_duration = 0
        for sample_count, sample_duration in sample_info_list:
            while sample_number <= sample_count:
                if track_type == TrackType.VIDEO and chunk_duration >= _SEGMENT_DURATION * timescale and str(sample_number) in key_frames_numbers:
                    chunk_durations.append(chunk_duration / timescale)
                    chunk_duration = 0
                elif chunk_duration > _SEGMENT_DURATION * timescale:
                    chunk_durations.append(chunk_duration / timescale)
                    chunk_duration = 0
                chunk_duration += sample_duration
                sample_number += 1

        chunk_durations.append(chunk_duration / timescale)

        return chunk_durations
