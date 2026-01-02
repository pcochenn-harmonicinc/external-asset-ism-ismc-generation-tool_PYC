from typing import List, Optional
import re

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger
from external_asset_ism_ismc_generation_tool.azure_client.azure_blob_service_client import AzureBlobServiceClient
from external_asset_ism_ismc_generation_tool.text_data_parser.vtt_to_imsc1_converter import VttToImsc1Converter
from external_asset_ism_ismc_generation_tool.text_data_parser.imsc1_segmenter import Imsc1Segmenter
from external_asset_ism_ismc_generation_tool.text_data_parser.cmft_packager import CmftPackager
from external_asset_ism_ismc_generation_tool.media_data_parser.media_box_extractor.media_box_extractor import MediaBoxExtractor

from external_asset_ism_ismc_generation_tool.common.common import Common
from external_asset_ism_ismc_generation_tool.media_data_parser.model.media_format import MediaFormat


class VttToCmftConverter:
    """Orchestrates the conversion of WebVTT files to CMFT format."""
    
    __logger: ILogger = Logger("VttToCmftConverter")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def __extract_language_from_filename(filename: str) -> str:
        """
        Extract 3-letter language code from filename.
        Searches for any 3-letter code separated by underscores or other delimiters.
        
        Args:
            filename: VTT filename (e.g., 'espn1_ARA.vtt')
            
        Returns:
            ISO 639-2/T language code or 'und' if not found
        """
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Split by underscores and other common delimiters
        parts = re.split(r'[_\-\.]', name_without_ext)
        
        # Search through all parts for a 3-letter code
        for part in parts:
            if len(part) == 3 and part.isalpha():
                return part.lower()
        
        return 'und'

    @staticmethod
    def convert_vtt_files_in_container(az_blob_service_client: AzureBlobServiceClient) -> List[str]:
        """
        Find and convert all WebVTT files in the Azure container to CMFT format.
        
        Args:
            az_blob_service_client: Azure blob service client
            
        Returns:
            List of CMFT filenames created
        """
        VttToCmftConverter.__logger.info("Starting WebVTT to CMFT conversion process")
        
        try:
            # Get list of all blobs
            blobs = az_blob_service_client.get_list_of_blobs()
            if not blobs:
                VttToCmftConverter.__logger.warning("No blobs found in container")
                return []
            
            # Find VTT files and video files
            vtt_files = []
            video_files = []
            
            for blob in blobs:
                VttToCmftConverter.__logger.info(f"Processing blob: {blob.name}")
                key, format_ext = Common.get_key_and_format(blob.name)
                VttToCmftConverter.__logger.info(f"Extracted key: {key}, format: {format_ext}")
                format_lower = format_ext.lower()
                
                VttToCmftConverter.__logger.info(f"Blob: {blob.name}, format: {format_ext}")
                
                if format_lower == MediaFormat.VTT.value.lower():
                    vtt_files.append(blob.name)
                # Check for all video file formats
                elif format_lower in [MediaFormat.MP4.value.lower(), 
                                     MediaFormat.MPI.value.lower(),
                                     MediaFormat.ISMV.value.lower(),
                                     MediaFormat.ISMA.value.lower()]:
                    video_files.append(blob.name)
            
            if not vtt_files:
                VttToCmftConverter.__logger.info("No VTT files found in container")
                return []
            
            VttToCmftConverter.__logger.info(f"Found {len(vtt_files)} VTT file(s): {vtt_files}")
            
            if not video_files:
                VttToCmftConverter.__logger.error(f"No video/media files found - cannot determine segment duration")
                raise ValueError("No video files found in container to determine segment duration")
            
            # Set fixed segment duration
            segment_duration = 4.0
            
            VttToCmftConverter.__logger.info(f"Using segment duration: {segment_duration}s")
            
            # Convert each VTT file
            created_files = []
            for vtt_filename in vtt_files:
                try:
                    cmft_filename = VttToCmftConverter.convert_vtt_to_cmft(
                        vtt_filename,
                        az_blob_service_client,
                        segment_duration
                    )
                    created_files.append(cmft_filename)
                except Exception as e:
                    VttToCmftConverter.__logger.error(f"Failed to convert {vtt_filename}: {e}")
                    # Continue with other files
            
            VttToCmftConverter.__logger.info(f"Successfully converted {len(created_files)} VTT file(s) to CMFT")
            return created_files
            
        except Exception as e:
            VttToCmftConverter.__logger.error(f"Error in VTT to CMFT conversion process: {e}")
            raise

    @staticmethod
    def convert_vtt_to_cmft(
        vtt_filename: str,
        az_blob_service_client: AzureBlobServiceClient,
        segment_duration: float
    ) -> str:
        """
        Convert a single WebVTT file to CMFT format.
        
        Args:
            vtt_filename: Name of the VTT file in the container
            az_blob_service_client: Azure blob service client
            segment_duration: Duration of each segment in seconds
            
        Returns:
            Name of the created CMFT file
        """
        VttToCmftConverter.__logger.info(f"Converting {vtt_filename} to CMFT")
        
        try:
            # 1. Download VTT content
            vtt_content = az_blob_service_client.download_part_of_blob(blob_name=vtt_filename)
            vtt_content = vtt_content.decode("utf-8")
            
            # Remove BOM if present
            if vtt_content.startswith('\ufeff'):
                vtt_content = vtt_content[1:]
            
            VttToCmftConverter.__logger.info(f"Downloaded VTT file: {len(vtt_content)} bytes")
            
            # Extract language code from filename
            language_code = VttToCmftConverter.__extract_language_from_filename(vtt_filename)
            VttToCmftConverter.__logger.info(f"Language code for IMSC1: {language_code}")
            
            # 2. Convert VTT to IMSC1
            imsc1_content = VttToImsc1Converter.convert(vtt_content, language_code)
            VttToCmftConverter.__logger.info("Converted VTT to IMSC1")
            
            # Generate IMSC1 filename
            imsc1_filename = vtt_filename.rsplit('.', 1)[0] + '.imsc1'

            with open(imsc1_filename, 'wb') as f:
                f.write(imsc1_content.encode('utf-8'))
            
            # 3. Segment IMSC1
            segments = Imsc1Segmenter.segment(imsc1_content, segment_duration)
            VttToCmftConverter.__logger.info(f"Segmented IMSC1 into {len(segments)} segments")
            
            # Generate IMSC1 segmented filename
            imsc1_segmented_filename = vtt_filename.rsplit('.', 1)[0] + '.imsc1seg'

            with open(imsc1_segmented_filename, 'wb') as f:
                for idx, (start_time, imsc1_xml) in enumerate(segments):
                    # Convert XML to bytes
                    xml_bytes = imsc1_xml.encode('utf-8')
                    f.write(xml_bytes)
            
            if not segments:
                VttToCmftConverter.__logger.warning("No segments created - empty subtitle file?")
                raise ValueError("No segments created from VTT file")
            
            # Calculate total duration from segments
            if segments:
                last_start, _ = segments[-1]
                total_duration = last_start + segment_duration
            else:
                total_duration = 0.0
            
            # 4. Package into CMFT
            # Extract language code from VTT filename
            language_code = VttToCmftConverter.__extract_language_from_filename(vtt_filename)
            VttToCmftConverter.__logger.info(f"Extracted language code: {language_code}")
            
            cmft_data = CmftPackager.package(segments, timescale=10000000, total_duration=total_duration, language_code=language_code)
            VttToCmftConverter.__logger.info(f"Packaged CMFT: {len(cmft_data)} bytes")
            
            # 5. Generate CMFT filename
            cmft_filename = vtt_filename.rsplit('.', 1)[0] + '.cmft'
            
            # 6. Upload to Azure container
            # Note: upload_blob_to_container expects string, but we have bytes
            # We need to upload bytes directly using the blob client
            blob_client = az_blob_service_client.container_client.get_blob_client(cmft_filename)
            blob_client.upload_blob(cmft_data, overwrite=True)
            VttToCmftConverter.__logger.info(f"Uploaded {cmft_filename} to container")
            
            # 7. Save local copy for verification
            with open(cmft_filename, 'wb') as f:
                f.write(cmft_data)
            VttToCmftConverter.__logger.info(f"Saved local copy: {cmft_filename}")
            
            return cmft_filename
            
        except Exception as e:
            VttToCmftConverter.__logger.error(f"Error converting {vtt_filename} to CMFT: {e}")
            raise ValueError(f"Failed to convert {vtt_filename} to CMFT: {e}")
