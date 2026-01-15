from typing import Optional

from construct import Container

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.model.atom.avcc_atom import Avcc
from external_asset_ism_ismc_generation_tool.media_data_parser.model.atom.hvcc_atom import Hvcc


class AtomsDataParser:
    __logger: ILogger = Logger("AtomsDataParser")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def parse_avcc(avcc_box: Container) -> Optional[Avcc]:
        if not avcc_box:
            return None

        configuration_version = avcc_box.version
        profile = avcc_box.profile
        profile_compatibility = avcc_box.compatibility
        level = avcc_box.level
        nalu_length_size = 1 + avcc_box.nal_unit_length_field
        sequence_parameters = avcc_box.sps.hex()
        picture_parameter = avcc_box.pps.hex()
        return Avcc(configuration_version, profile, profile_compatibility, level, nalu_length_size, sequence_parameters, picture_parameter)
    
    @staticmethod
    def parce_hvcc_data(hvcc_box: Container) -> Optional[Hvcc]:
        if not hvcc_box:
            return None

        configuration_version = hvcc_box.version
        general_profile_space = hvcc_box.profile_space
        general_tier_flag = hvcc_box.general_tier_flag
        general_profile = hvcc_box.general_profile
        general_profile_compatibility_flags = hvcc_box.general_profile_compatibility_flags
        general_constraint_indicator_flags = hvcc_box.general_constraint_indicator_flags
        general_level = hvcc_box.general_level
        min_spatial_segmentation = hvcc_box.min_spatial_segmentation
        parallelism_type = hvcc_box.parallelism_type
        chroma_format = hvcc_box.chroma_format
        luma_bit_depth = 8 + hvcc_box.luma_bit_depth
        chroma_bit_depth = 8 + hvcc_box.chroma_bit_depth
        average_frame_rate = hvcc_box.average_frame_rate
        constant_frame_rate = hvcc_box.constant_frame_rate
        num_temporal_layers = hvcc_box.num_temporal_layers
        temporal_id_nested = hvcc_box.temporal_id_nested
        nalu_length_size = 1 + hvcc_box.nalu_length_size
        nalus = AtomsDataParser.parse_nal_units(hvcc_box.raw_bytes)

        return Hvcc(configuration_version,
                    general_profile_space,
                    general_profile,
                    general_tier_flag,
                    general_profile_compatibility_flags,
                    general_constraint_indicator_flags,
                    general_level,
                    min_spatial_segmentation,
                    parallelism_type,
                    chroma_format,
                    chroma_bit_depth,
                    luma_bit_depth,
                    average_frame_rate,
                    constant_frame_rate,
                    num_temporal_layers,
                    temporal_id_nested,
                    nalu_length_size,
                    nalus)

    @staticmethod
    def parse_nal_units(raw_bytes: bytes) -> Optional[list]:
        num_seq = raw_bytes[0]
        current = 1
        nalus = []

        for _ in range(num_seq):
            # skip this byte as we don't use data from it
            array_completeness = raw_bytes[current] >> 7 & 0x01 # first bit of a byte
            reserved = (raw_bytes[current] >> 6) & 0x01
            nalu_type = raw_bytes[current] & 0x3F # last 6 bits of a byte
            current += 1

            nalu_count = int.from_bytes(raw_bytes[current:current + 2], 'big')
            current += 2

            for _ in range(0, nalu_count):
                nalu_length = int.from_bytes(raw_bytes[current:current + 2], 'big')
                current += 2
                nalus.append(raw_bytes[current:current + nalu_length])
                current += nalu_length
        return nalus
