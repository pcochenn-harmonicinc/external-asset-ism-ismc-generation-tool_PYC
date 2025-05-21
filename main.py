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


def generate_manifests():
    logger: Logger = Logger("main")

    settings_from_cli_arguments = CliArgumentsParser.parse()
    settings_from_config_file = ConfigFileParser.parse()
    settings = Common.merge_dicts([settings_from_config_file, settings_from_cli_arguments])
    az_blob_service_client: AzureBlobServiceClient = AzureBlobServiceClient(settings)
    blob_media_data : BlobMediaData = BlobDataHandler.get_data_from_blobs(az_blob_service_client)

    media_data: MediaData = MediaDataParser.get_media_data(blob_media_data.media_datas, blob_media_data.media_index_datas, settings['is_multithreading'])

    # Generate and upload server manifest (.ism)
    server_manifest_name = f'{blob_media_data.manifest_name}.ism'
    if not az_blob_service_client.blob_exists(server_manifest_name):
        audios = IsmGenerator.get_audios(media_track_infos=media_data.media_track_info_list)
        videos = IsmGenerator.get_videos(media_track_infos=media_data.media_track_info_list)
        text_streams = IsmGenerator.get_text_streams(media_data.media_track_info_list, blob_media_data.text_data_info_list)
        ism_xml_string = IsmGenerator.generate(blob_media_data.manifest_name, audios=audios, videos=videos, text_streams=text_streams)
        az_blob_service_client.upload_blob_to_container(server_manifest_name, ism_xml_string)
        logger.info(f"{server_manifest_name} is created and stored to the {az_blob_service_client.container_client.container_name} container")
    else:
        logger.warning(f"{server_manifest_name} already exists")

    # Generate and upload client manifest (.ismc)
    client_manifest_name = f'{blob_media_data.manifest_name}.ismc'
    if not az_blob_service_client.blob_exists(client_manifest_name):
        ismc_xml_string = IsmcGenerator.generate(duration=media_data.media_duration, media_track_infos=media_data.media_track_info_list, text_data_info_list=blob_media_data.text_data_info_list)
        az_blob_service_client.upload_blob_to_container(client_manifest_name, ismc_xml_string)
        logger.info(f"{client_manifest_name} is created and stored to the {az_blob_service_client.container_client.container_name} container")
    else:
        logger.warning(f"{client_manifest_name} already exists")


if __name__ == '__main__':
    generate_manifests()
