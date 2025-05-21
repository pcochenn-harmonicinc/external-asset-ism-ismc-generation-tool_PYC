from typing import List

from tools.pymp4.src.pymp4.parser import Box

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.model.four_cc import FourCC
from external_asset_ism_ismc_generation_tool.media_data_parser.model.track_format import TrackFormat
from external_asset_ism_ismc_generation_tool.media_data_parser.atom_parser.audio_parser import AudioParser
from external_asset_ism_ismc_generation_tool.media_data_parser.model.audio_track_data import AudioTrackData
from external_asset_ism_ismc_generation_tool.media_data_parser.atom_parser.descriptor_parser import DescriptorParser
from external_asset_ism_ismc_generation_tool.media_data_parser.model.descriptor.dec3_descriptor import DEC3Descriptor


class DEC3Parser(AudioParser):
    __logger: ILogger = Logger("DEC3Parser")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    def __init__(self, audio_data: Box):
        super().__init__(audio_data)
        self.audio_format = TrackFormat.EC_3.value

    def get_audio_track_data(self, calculated_bit_rate: int) -> AudioTrackData:
        four_cc = FourCC.EC_3.value
        bit_rate = calculated_bit_rate
        dec3_data = self.audio_data.data
        descriptors: List[DEC3Descriptor] = DescriptorParser.get_dec3_descriptors(dec3_data)

        # implement logic for several descriptors if needed
        if len(descriptors) > 1:
            DEC3Parser.__logger.error(f'Detected {len(descriptors)} dec3 substreams.')
            raise ValueError("More than 1 dec3 (eac-3) descriptors detected.")
        descriptor = descriptors[0]
        return AudioTrackData(descriptor.codec_private_data,
                              bit_rate,
                              four_cc,
                              descriptor.channels,
                              descriptor.data_rate,
                              descriptor.sample_rate)