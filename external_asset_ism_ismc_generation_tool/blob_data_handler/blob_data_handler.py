from typing import Dict, Union, Tuple, Optional
from os import cpu_count
from concurrent.futures import ThreadPoolExecutor

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.common.common import Common
from external_asset_ism_ismc_generation_tool.azure_client.azure_blob_service_client import AzureBlobServiceClient
from external_asset_ism_ismc_generation_tool.file_processor.file_processor import FileProcessor
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_format import MediaFormat
from external_asset_ism_ismc_generation_tool.blob_data_handler.model.blob_media_data import BlobMediaData
from external_asset_ism_ismc_generation_tool.text_data_parser.model.text_data_info import TextDataInfo


class BlobDataHandler:
    __logger: ILogger = Logger("BlobDataHandler")
    
    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def get_data_from_blobs(az_blob_service_client: AzureBlobServiceClient) -> BlobMediaData:
        BlobDataHandler.__logger.info(msg="Get blobs list from Azure container")
        blobs = az_blob_service_client.get_list_of_blobs()
        if blobs is None:
            BlobDataHandler.__logger.error(msg=f"Cannot find blobs inside the container {az_blob_service_client.container_client.container_name}")
            raise ValueError(f"Cannot find blobs inside the container {az_blob_service_client.container_client.container_name}")

        executor = None
        try:
            if az_blob_service_client.is_multithreading:
                threads_num = cpu_count()
                executor = ThreadPoolExecutor(max_workers=threads_num)
            blob_media_data: BlobMediaData = BlobDataHandler.__process_blobs(blobs, az_blob_service_client, executor)

        finally:
            if executor:
                executor.shutdown()

        return blob_media_data

    @staticmethod
    def __process_blobs(blobs, az_blob_service_client: AzureBlobServiceClient, executor: ThreadPoolExecutor) -> BlobMediaData:
        manifest_name = ""
        media_datas = None
        media_index_datas = None
        text_datas_info = []

        task_mapping = BlobDataHandler.__map_blob_tasks(blobs, az_blob_service_client, executor)

        for task in Common.get_completed_tasks(task_mapping, executor):
            blob_name = task_mapping[task] if executor else task
            try:
                key, result = task.result() if executor else task_mapping[task]
                manifest_name = manifest_name or key

                if MediaFormat.is_media_format(blob_name):
                    if not MediaFormat.is_mpi_format(blob_name):
                        media_datas = Common.merge_dicts([media_datas, result])
                    else:
                        media_index_datas = Common.merge_dicts([media_index_datas, result])
                elif MediaFormat.is_text_format(blob_name):
                    text_datas_info.append(result)
            except Exception as e:
                BlobDataHandler.__logger.error(f"Error processing blob {blob_name}: {e}")

        return BlobMediaData(manifest_name, media_datas, media_index_datas, text_datas_info)

    @staticmethod
    def __process_blob(blob, az_blob_service_client: AzureBlobServiceClient) -> Tuple[Optional[str], Optional[Union[Dict[str, Dict], TextDataInfo]]]:
        BlobDataHandler.__logger.info(msg=f"Handle blob {blob.name}")
        key, format = Common.get_key_and_format(blob.name)
        result = FileProcessor.process_file(format, blob.name, az_blob_service_client)
        return key, result

    @staticmethod
    def __map_blob_tasks(blobs, az_blob_service_client: AzureBlobServiceClient, executor: ThreadPoolExecutor) -> any:
        if executor:
            return {executor.submit(BlobDataHandler.__process_blob, blob, az_blob_service_client): blob.name for blob in blobs}
        else:
            return {blob.name: BlobDataHandler.__process_blob(blob, az_blob_service_client) for blob in blobs}
