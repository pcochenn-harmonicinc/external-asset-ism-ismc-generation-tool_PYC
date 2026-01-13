from external_asset_ism_ismc_generation_tool.common.common import Common
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.settings_parser.cli_arguments_parser import CliArgumentsParser
from external_asset_ism_ismc_generation_tool.settings_parser.config_file_parser import ConfigFileParser
from external_asset_ism_ismc_generation_tool.azure_client.azure_blob_service_client import AzureBlobServiceClient

def remove_azure_asset(settings: dict):
    logger: Logger = Logger("main")

    az_blob_service_client: AzureBlobServiceClient = AzureBlobServiceClient(settings)

    # Cleanup: Delete the containers and their contents after the test
    try:
        container_name = settings["container_name"]
    except KeyError as exc:
        missing_key = exc.args[0] if exc.args else "unknown"
        logger.error(f"Required setting '{missing_key}' is missing.")
        raise ValueError(f"Missing required setting: {missing_key}") from exc

    container_client = az_blob_service_client.blob_service_client.get_container_client(container_name)
    try:
        container_client.delete_container()
        logger.info(f"Container {container_name} is deleted")
        print(f"Container {container_name} is deleted")
    except Exception as exc:
        logger.error(f"Failed to delete container {container_name}: {exc}")
        print(f"Failed to delete container {container_name}. See logs for details.")


if __name__ == '__main__':
    settings_from_cli_arguments = CliArgumentsParser.parse()
    settings_from_config_file = ConfigFileParser.parse()
    settings = Common.merge_dicts([settings_from_config_file, settings_from_cli_arguments])

    remove_azure_asset(settings)
