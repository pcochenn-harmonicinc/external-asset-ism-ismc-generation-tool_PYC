from typing import Optional, Dict, Union
from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.azure_client.azure_blob_service_client import AzureBlobServiceClient
from external_asset_ism_ismc_generation_tool.media_data_parser.azure_media_data_parser import AzureMediaDataParser
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_format import MediaFormat
from external_asset_ism_ismc_generation_tool.text_data_parser.text_data_parser import TextDataParser
from external_asset_ism_ismc_generation_tool.text_data_parser.model.text_data_info import TextDataInfo


class FileProcessor:
    __logger: ILogger = Logger("FileProcessor")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def process_file(format: str, blob_name: str, az_blob_service_client: AzureBlobServiceClient) -> Optional[Union[Dict[str, Dict], TextDataInfo]]:
        func = FileProcessor.__function_map.get(format)
        if func:
            return func(blob_name, az_blob_service_client)
        FileProcessor.__logger.info(f'Cannot parse file {blob_name} with format: {format}')
        return None

    @staticmethod
    def __process_media_file(blob_name: str, az_blob_service_client: AzureBlobServiceClient) -> Dict[str, Dict]:
        media_data = {blob_name: AzureMediaDataParser.get_media_data(az_blob_service_client, blob_name)}
        return media_data

    @staticmethod
    def __process_ttml_vtt(blob_name: str, az_blob_service_client: AzureBlobServiceClient) -> Optional[TextDataInfo]:
        text_data_info = TextDataParser.get_text_data_info(blob_name, az_blob_service_client)
        return text_data_info

    __function_map = {
        MediaFormat.MP4.value: __process_media_file,
        MediaFormat.MPI.value: __process_media_file,
        MediaFormat.ISMV.value: __process_media_file,
        MediaFormat.ISMA.value: __process_media_file,
        MediaFormat.TTML.value: __process_ttml_vtt,
        MediaFormat.VTT.value: __process_ttml_vtt,
        MediaFormat.CMFT.value: __process_media_file
    }
