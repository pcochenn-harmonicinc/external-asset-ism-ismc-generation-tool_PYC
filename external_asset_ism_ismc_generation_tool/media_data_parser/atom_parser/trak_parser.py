from tools.pymp4.src.pymp4.parser import Box

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.model.track_type import TrackType
from external_asset_ism_ismc_generation_tool.media_data_parser.media_box_extractor.media_box_extractor import MediaBoxExtractor


class TRAKParser:
    __logger: ILogger = Logger("TRAKParser")
    __VIDEO_HANDLER_TYPE = b'vide'
    __AUDIO_HANDLER_TYPE = b'soun'

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    def __init__(self, trak_atom: Box):
        self.trak_atom = trak_atom

    def get_track_type(self) -> TrackType:

        mdia_atom = MediaBoxExtractor.get_mp4_sub_box(self.trak_atom, 'mdia')
        hdlr_atom = MediaBoxExtractor.get_mp4_sub_box(mdia_atom, 'hdlr')
        handler_type = hdlr_atom['handler_type']
        TRAKParser.__logger.info(f'Track type form the `trak` atom: {handler_type}')
        if handler_type == TRAKParser.__VIDEO_HANDLER_TYPE:
            return TrackType.VIDEO
        elif handler_type == TRAKParser.__AUDIO_HANDLER_TYPE:
            return TrackType.AUDIO
        else:
            return TrackType.TEXT

    def get_timescale(self) -> int:
        mdia_atom = MediaBoxExtractor.get_mp4_sub_box(self.trak_atom, 'mdia')
        mdhd_atom = MediaBoxExtractor.get_mp4_sub_box(mdia_atom, 'mdhd')
        return mdhd_atom['timescale']

    def get_track_id(self) -> int:
        tkhd_atom = MediaBoxExtractor.get_mp4_sub_box(self.trak_atom, 'tkhd')
        return tkhd_atom['track_ID']

    def get_track_language(self) -> str:
        mdia_atom = MediaBoxExtractor.get_mp4_sub_box(self.trak_atom, 'mdia')
        mvhd_atom = MediaBoxExtractor.get_mp4_sub_box(mdia_atom, 'mdhd')
        return mvhd_atom['language']
