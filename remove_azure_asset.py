from external_asset_ism_ismc_generation_tool.common.common import Common
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.media_data_parser.media_data_parser import MediaDataParser
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_data import MediaData
from external_asset_ism_ismc_generation_tool.blob_data_handler.blob_data_handler import BlobDataHandler
from external_asset_ism_ismc_generation_tool.mss_client_manifest.ismc_generator import IsmcGenerator
from external_asset_ism_ismc_generation_tool.mss_server_manifest.ism_generator import IsmGenerator
from external_asset_ism_ismc_generation_tool.settings_parser.cli_arguments_parser import CliArgumentsParser
from external_asset_ism_ismc_generation_tool.settings_parser.config_file_parser import ConfigFileParser
from external_asset_ism_ismc_generation_tool.azure_client.azure_blob_service_client import AzureBlobServiceClient
from external_asset_ism_ismc_generation_tool.blob_data_handler.model.blob_media_data import BlobMediaData

def remove_azure_asset(settings: dict):
    logger: Logger = Logger("main")

    az_blob_service_client: AzureBlobServiceClient = AzureBlobServiceClient(settings)

    # Cleanup: Delete the containers and their contents after the test
    container_name = settings['container_name']

    container_client = az_blob_service_client.blob_service_client.get_container_client(container_name)
    container_client.delete_container()
    logger.info(f"Container {container_name} is deleted")
    print(f"Container {container_name} is deleted")


if __name__ == '__main__':
    settings_from_cli_arguments = CliArgumentsParser.parse()
    settings_from_config_file = ConfigFileParser.parse()
    settings = Common.merge_dicts([settings_from_config_file, settings_from_cli_arguments])

    remove_azure_asset(settings)
