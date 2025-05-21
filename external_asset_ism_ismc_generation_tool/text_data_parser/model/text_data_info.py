from external_asset_ism_ismc_generation_tool.common.base_model import BaseModel


class TextDataInfo(BaseModel):
    name: str
    start_time: int
    duration: float
    bit_rate: int

    def __init__(self, name: str,
                 start_time: int,
                 duration: float,
                 bit_rate: int):
        self.name = name
        self.start_time = start_time
        self.duration = duration
        self.bit_rate = bit_rate

