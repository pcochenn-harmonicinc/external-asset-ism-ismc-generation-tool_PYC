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

import zipfile

# It is assumed there is at least one folder in the top level of the zip file
# and the folder name would be used to create container, the content inside the folder would be uploaded to the container
def upload_azure_asset(settings: dict):
    logger: Logger = Logger("main")

    az_blob_service_client: AzureBlobServiceClient = AzureBlobServiceClient(settings)

    container_name = settings['container_name']
    zip_file_name = settings['asset_zip_name']


    # Extract top-level folders from the zip file
    with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:

        # create container if it does not exist
        container_client = az_blob_service_client.blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
            logger.info(f"Container {container_name} is created")
            print(f"Container {container_name} is created")
        else:
            logger.info(f"Container {container_name} already exists")
            print(f"Container {container_name} already exists")

        # Extract files from the zip file and upload to Azurite
        file_names = zip_ref.namelist()

        for file_name in file_names:
            # upload blob
            blob_client = az_blob_service_client.blob_service_client.get_blob_client(
                container=container_name, blob=file_name
            )
            with zip_ref.open(file_name) as blob_data:
                if not blob_client.exists():
                    blob_client.upload_blob(
                        blob_data
                    )
                    logger.info(f"Blob {file_name} is uploaded to container {container_name}")
                    print(f"Blob {file_name} is uploaded to container {container_name}")
                else:
                    logger.info(f"Blob {file_name} already exists in container {container_name}")
                    print(f"Blob {file_name} already exists in container {container_name}")

if __name__ == '__main__':
    settings_from_cli_arguments = CliArgumentsParser.parse()
    settings_from_config_file = ConfigFileParser.parse()
    settings = Common.merge_dicts([settings_from_config_file, settings_from_cli_arguments])

    upload_azure_asset(settings)
