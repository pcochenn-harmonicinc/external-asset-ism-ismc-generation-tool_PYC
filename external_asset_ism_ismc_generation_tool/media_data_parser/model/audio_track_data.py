from typing import Optional

from external_asset_ism_ismc_generation_tool.common.base_model import BaseModel


class AudioTrackData(BaseModel):
    channels: int
    data_rate: int
    codec_private_data: str
    bit_rate : int
    four_cc: str
    sample_rate: int

    def __init__(self,
                 codec_private_data: str,
                 bit_rate: int,
                 four_cc: str,
                 channels: Optional[int] = 0,
                 data_rate: Optional[int] = 0,
                 sample_rate: Optional[int] = 0):
        self.codec_private_data = codec_private_data
        self.bit_rate = bit_rate
        self.four_cc = four_cc
        self.channels = channels
        self.data_rate = data_rate
        self.sample_rate = sample_rate
