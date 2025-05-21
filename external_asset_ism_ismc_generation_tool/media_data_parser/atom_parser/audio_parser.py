from tools.pymp4.src.pymp4.parser import Box

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.model.audio_track_data import AudioTrackData


class AudioParser:
    __logger: ILogger = Logger("AudioParser")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    def __init__(self, audio_data: Box):
        self.audio_data = audio_data

    def get_audio_track_data(self, calculated_bit_rate: int) -> AudioTrackData:
        raise ValueError("Parent class function wasn't overriden")
