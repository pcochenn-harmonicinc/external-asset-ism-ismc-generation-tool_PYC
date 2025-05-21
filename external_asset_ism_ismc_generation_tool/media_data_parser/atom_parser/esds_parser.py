from tools.pymp4.src.pymp4.parser import Box

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.atom_parser.audio_decoder_specific_info_parser import AudioAacDecoderSpecificInfoParser
from external_asset_ism_ismc_generation_tool.media_data_parser.atom_parser.descriptor_parser import DescriptorParser
from external_asset_ism_ismc_generation_tool.media_data_parser.model.audio_object_type import AudioObjectType
from external_asset_ism_ismc_generation_tool.media_data_parser.model.descriptor.descriptor_type import DescriptorType
from external_asset_ism_ismc_generation_tool.media_data_parser.model.four_cc import FourCC
from external_asset_ism_ismc_generation_tool.media_data_parser.model.track_format import TrackFormat
from external_asset_ism_ismc_generation_tool.media_data_parser.atom_parser.audio_parser import AudioParser
from external_asset_ism_ismc_generation_tool.media_data_parser.model.audio_track_data import AudioTrackData


class ESDSParser(AudioParser):
    __logger: ILogger = Logger("ESDSParser")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    def __init__(self, audio_data: Box):
        super().__init__(audio_data)
        self.audio_format = TrackFormat.MP4A.value

    def get_audio_track_data(self, calculated_bit_rate: int) -> AudioTrackData:
        four_cc = FourCC.AAC.value
        codec_private_data = ''
        bit_rate = calculated_bit_rate
        esds_data = self.audio_data.data
        descriptors = DescriptorParser.get_esds_descriptors(esds_data[4:])
        for descriptor in descriptors:
            if descriptor.tag == DescriptorType.ES_DESCRIPTOR_DECODER_CONFIG.value:
                bit_rate = descriptor.avg_bitrate
            elif descriptor.tag == DescriptorType.ES_DESCRIPTOR_DECODER_SPECIFIC_INFO.value:
                codec_private_data = descriptor.decoder_specific_info.hex()
                parsed_decoder_specific_info = AudioAacDecoderSpecificInfoParser.parse_audio_decoder_specific_info(descriptor.decoder_specific_info)
                if parsed_decoder_specific_info:
                    if parsed_decoder_specific_info.object_type == AudioObjectType.MPEG4_AUDIO_OBJECT_TYPE_SBR:
                        four_cc = FourCC.AAC_CL.value
                        ## for future when support for AACH and AACP is needed just uncomment
                        # if parsed_decoder_specific_info.is_sbr_present and parsed_decoder_specific_info.is_ps_present:
                        #     four_cc = FourCC.AACP.value
                        # elif parsed_decoder_specific_info.is_sbr_present:
                        #     four_cc = FourCC.AAC_HE.value
                    elif parsed_decoder_specific_info.object_type == AudioObjectType.MPEG4_AUDIO_OBJECT_TYPE_AAC_LC:
                        four_cc = FourCC.AAC_CL.value
                    else:
                        four_cc = FourCC.AAC.value
        return AudioTrackData(codec_private_data, bit_rate, four_cc)
