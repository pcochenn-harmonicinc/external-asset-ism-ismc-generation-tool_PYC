import io
import re
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
    def _sanitize_html_tags(text: str) -> tuple[str, list[str]]:
        """
        Sanitize HTML tags in VTT cue text to prevent parsing errors.
        Removes malformed or unmatched closing tags.
        
        Args:
            text: Text potentially containing malformed HTML
            
        Returns:
            Tuple of (sanitized text, list of issues found)
        """
        issues = []
        
        # Valid VTT tags: b, i, u, ruby, rt, v, c, lang
        valid_tags = r'(?:b|i|u|ruby|rt|v|c|lang)'
        
        # Find and remove standalone closing tags (like </bad>)
        invalid_closing = re.findall(r'<\/(?!' + valid_tags + r'\b)[^>]*>', text)
        if invalid_closing:
            issues.append(f"Removed invalid closing tags: {', '.join(invalid_closing)}")
        text = re.sub(r'<\/(?!' + valid_tags + r'\b)[^>]*>', '', text)
        
        # Find and remove malformed opening tags (not matching valid VTT tags)
        invalid_opening = re.findall(r'<(?!' + valid_tags + r'\b|\/)[^>]*>', text)
        if invalid_opening:
            issues.append(f"Removed invalid opening tags: {', '.join(invalid_opening)}")
        text = re.sub(r'<(?!' + valid_tags + r'\b|\/)[^>]*>', '', text)
        
        return text, issues

    @staticmethod
    def _sanitize_vtt_content(vtt_content: str) -> tuple[str, list[str]]:
        """
        Sanitize entire VTT content by processing each cue's text.
        
        Args:
            vtt_content: Full VTT file content
            
        Returns:
            Tuple of (sanitized VTT content, list of all issues found)
        """
        lines = vtt_content.split('\n')
        sanitized_lines = []
        in_cue_text = False
        all_issues = []
        cue_number = 0
        
        for line in lines:
            # Check if this is a timing line (contains -->)
            if '-->' in line:
                in_cue_text = True
                cue_number += 1
                sanitized_lines.append(line)
            # Empty line marks end of cue
            elif not line.strip():
                in_cue_text = False
                sanitized_lines.append(line)
            # If we're in cue text, sanitize it
            elif in_cue_text:
                sanitized_text, issues = VttToImsc1Converter._sanitize_html_tags(line)
                if issues:
                    for issue in issues:
                        all_issues.append(f"Cue {cue_number}: {issue}")
                sanitized_lines.append(sanitized_text)
            # Header, cue identifiers, etc.
            else:
                sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines), all_issues

    @staticmethod
    def convert(vtt_content: str, language_code: str = 'und', sanitize_html: bool = True) -> tuple[str, list[str]]:
        """
        Convert WebVTT content to IMSC1 format.
        
        Args:
            vtt_content: String containing WebVTT subtitle data
            language_code: ISO 639-2/T 3-letter language code (default: 'und')
            sanitize_html: Whether to sanitize malformed HTML tags (default: True)
            
        Returns:
            Tuple of (IMSC1 XML string, list of sanitization warnings)
        """
        VttToImsc1Converter.__logger.info("Converting WebVTT to IMSC1")
        
        try:
            # Validate VTT content is not empty
            if not vtt_content or not vtt_content.strip():
                error_msg = "VTT content is empty or contains only whitespace"
                VttToImsc1Converter.__logger.error(error_msg)
                raise ValueError(f"Failed to convert WebVTT to IMSC1: {error_msg}")
            
            # Sanitize HTML tags if requested
            sanitization_issues = []
            if sanitize_html:
                VttToImsc1Converter.__logger.info("Sanitizing HTML tags in VTT content")
                vtt_content, sanitization_issues = VttToImsc1Converter._sanitize_vtt_content(vtt_content)
                
                if sanitization_issues:
                    VttToImsc1Converter.__logger.info(f"Sanitization fixed {len(sanitization_issues)} issue(s):")
                    for issue in sanitization_issues:
                        VttToImsc1Converter.__logger.info(f"  - {issue}")
                else:
                    VttToImsc1Converter.__logger.info("No HTML sanitization issues found")
            
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
            
            return imsc1_content, sanitization_issues
            
        except AttributeError as e:
            # Usually indicates malformed VTT structure or missing required elements
            error_msg = f"Malformed VTT structure - missing required elements or invalid format: {e}"
            VttToImsc1Converter.__logger.error(error_msg)
            VttToImsc1Converter.__logger.error("Check that the VTT file has proper WEBVTT header and valid cue structure")
            raise ValueError(f"Failed to convert WebVTT to IMSC1: {error_msg}")
            
        except TypeError as e:
            # Often indicates HTML parsing issues or invalid cue text
            error_msg = f"Invalid VTT content - malformed HTML tags or cue text: {e}"
            VttToImsc1Converter.__logger.error(error_msg)
            if not sanitize_html:
                VttToImsc1Converter.__logger.error("Consider enabling HTML sanitization (sanitize_html=True) to handle malformed tags")
            raise ValueError(f"Failed to convert WebVTT to IMSC1: {error_msg}")
            
        except UnicodeDecodeError as e:
            # Character encoding issues
            error_msg = f"VTT file encoding error: {e}"
            VttToImsc1Converter.__logger.error(error_msg)
            VttToImsc1Converter.__logger.error("Ensure the VTT file is UTF-8 encoded")
            raise ValueError(f"Failed to convert WebVTT to IMSC1: {error_msg}")
            
        except ValueError as e:
            # Re-raise ValueError (including our own validation errors)
            if "Failed to convert WebVTT to IMSC1" in str(e):
                raise
            error_msg = f"VTT validation error - invalid timing or format: {e}"
            VttToImsc1Converter.__logger.error(error_msg)
            VttToImsc1Converter.__logger.error("Check that all timestamps follow HH:MM:SS.mmm format with proper '-->' separator")
            raise ValueError(f"Failed to convert WebVTT to IMSC1: {error_msg}")
            
        except Exception as e:
            # Catch-all for unexpected errors
            error_type = type(e).__name__
            error_msg = f"Unexpected error during VTT conversion ({error_type}): {e}"
            VttToImsc1Converter.__logger.error(error_msg)
            VttToImsc1Converter.__logger.error(f"VTT content length: {len(vtt_content) if vtt_content else 0} bytes")
            raise ValueError(f"Failed to convert WebVTT to IMSC1: {error_msg}")



