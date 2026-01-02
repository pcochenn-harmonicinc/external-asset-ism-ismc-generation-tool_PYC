import io
import ttconv.vtt.reader as vtt_reader
import ttconv.imsc.writer as imsc_writer
from ttconv.imsc.config import IMSCWriterConfiguration, TimeExpressionSyntaxEnum

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger


class VttToImsc1Converter:
    """Converts WebVTT files to IMSC1 (TTML) format."""
    
    __logger: ILogger = Logger("VttToImsc1Converter")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def convert(vtt_content: str, language_code: str = 'und') -> str:
        """
        Convert WebVTT content to IMSC1 format.
        
        Args:
            vtt_content: String containing WebVTT subtitle data
            language_code: ISO 639-2/T 3-letter language code (default: 'und')
            
        Returns:
            String containing IMSC1 (TTML) formatted XML
        """
        VttToImsc1Converter.__logger.info("Converting WebVTT to IMSC1")
        
        try:
            # Parse VTT content using ttconv
            vtt_input = io.StringIO(vtt_content)
            doc = vtt_reader.to_model(vtt_input)
            
            # Create IMSC writer configuration with specified parameters
            # time_format: "clock_time" for HH:MM:SS.mmm format
            # fps: None means no frame-based timing
            config = IMSCWriterConfiguration(
                time_format=TimeExpressionSyntaxEnum.clock_time,
                fps=None
            )
            
            # Convert to IMSC1
            imsc1_tree = imsc_writer.from_model(doc, config)
            
            # Add xml:lang attribute to the root element
            root = imsc1_tree.getroot()
            root.set('{http://www.w3.org/XML/1998/namespace}lang', language_code)
            
            # Convert ElementTree to string
            # from_model returns an ElementTree, so we need to write it to a string
            output = io.BytesIO()
            imsc1_tree.write(output, encoding='utf-8', xml_declaration=True)
            imsc1_content = output.getvalue().decode('utf-8')
            
            VttToImsc1Converter.__logger.info("Successfully converted WebVTT to IMSC1")
            
            return imsc1_content
            
        except Exception as e:
            VttToImsc1Converter.__logger.error(f"Error converting WebVTT to IMSC1: {e}")
            raise ValueError(f"Failed to convert WebVTT to IMSC1: {e}")



