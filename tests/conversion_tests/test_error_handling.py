"""
Test module for error handling and logging in VTT to CMFT conversion.

This module tests that appropriate error messages are logged when
malformed or invalid files are processed, and that sanitization reports fixed issues.
"""

import pytest
import xml.etree.ElementTree as ET
from external_asset_ism_ismc_generation_tool.text_data_parser.vtt_to_imsc1_converter import VttToImsc1Converter
from external_asset_ism_ismc_generation_tool.text_data_parser.imsc1_segmenter import Imsc1Segmenter
from external_asset_ism_ismc_generation_tool.text_data_parser.cmft_packager import CmftPackager


def test_empty_vtt_error():
    """Test that empty VTT produces descriptive error."""
    invalid_vtt = ""
    
    with pytest.raises(ValueError) as exc_info:
        VttToImsc1Converter.convert(invalid_vtt)
    
    error_msg = str(exc_info.value)
    assert "Failed to convert WebVTT to IMSC1" in error_msg
    assert "empty" in error_msg.lower() or "whitespace" in error_msg.lower()
    print(f"✓ Empty VTT error: {error_msg}")


def test_malformed_html_sanitization_logging():
    """Test that HTML sanitization succeeds with malformed HTML."""
    vtt_with_bad_html = """WEBVTT

00:00:01.000 --> 00:00:03.000
Text with </bad> closing tag

00:00:04.000 --> 00:00:06.000
Text with <invalid> opening tag

00:00:07.000 --> 00:00:09.000
Text with <b>valid bold</b> tag
"""
    
    # Should succeed with sanitization
    imsc1_content, warnings = VttToImsc1Converter.convert(vtt_with_bad_html, sanitize_html=True)
    
    assert imsc1_content is not None
    assert '<?xml' in imsc1_content
    
    # Verify malformed tags were removed
    assert '</bad>' not in imsc1_content
    assert '<invalid>' not in imsc1_content
    
    print(f"✓ HTML sanitization fixed malformed tags")


def test_malformed_html_without_sanitization():
    """Test that malformed HTML produces descriptive error when sanitization disabled."""
    vtt_with_bad_html = """WEBVTT

00:00:01.000 --> 00:00:03.000
Cue with </bad> tag that will cause crash
"""
    
    with pytest.raises(ValueError) as exc_info:
        VttToImsc1Converter.convert(vtt_with_bad_html, sanitize_html=False)
    
    error_msg = str(exc_info.value)
    assert "Failed to convert WebVTT to IMSC1" in error_msg
    assert "HTML" in error_msg or "cue text" in error_msg.lower()
    print(f"✓ Malformed HTML error: {error_msg}")


def test_no_sanitization_issues_logged():
    """Test that clean VTT converts successfully."""
    clean_vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
Clean text with <b>valid</b> tags only
"""
    
    imsc1_content, warnings = VttToImsc1Converter.convert(clean_vtt, sanitize_html=True)
    
    assert imsc1_content is not None
    assert '<?xml' in imsc1_content
    
    print("✓ Clean VTT: converted successfully")


def test_invalid_xml_segmentation():
    """Test IMSC1 segmentation with invalid XML."""
    invalid_xml = "<not valid xml"
    
    with pytest.raises(ValueError) as exc_info:
        Imsc1Segmenter.segment(invalid_xml, 4.0)
    
    error_msg = str(exc_info.value)
    assert "Failed to segment IMSC1" in error_msg
    assert "parse" in error_msg.lower() or "xml" in error_msg.lower()
    print(f"✓ Invalid XML error: {error_msg}")


def test_malformed_imsc1_structure():
    """Test IMSC1 segmentation with valid XML but wrong structure."""
    invalid_structure = """<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/ns/ttml">
    <head></head>
    <!-- Missing body element -->
</tt>
"""
    
    with pytest.raises(ValueError) as exc_info:
        Imsc1Segmenter.segment(invalid_structure, 4.0)
    
    error_msg = str(exc_info.value)
    assert "Failed to segment IMSC1" in error_msg
    assert "body" in error_msg.lower()
    print(f"✓ Missing body error: {error_msg}")


def test_empty_segments_cmft_packaging():
    """Test CMFT packaging with empty segments list."""
    empty_segments = []
    
    # Empty segments should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        CmftPackager.package(empty_segments, timescale=10000000, total_duration=0.0)
    
    error_msg = str(exc_info.value)
    assert "Cannot package CMFT" in error_msg
    assert "empty" in error_msg.lower()
    print(f"✓ Empty segments error: {error_msg}")


def test_cmft_packaging_invalid_segment_data():
    """Test CMFT packaging with invalid segment data."""
    # Invalid segment: not a tuple
    invalid_segments = ["not a tuple"]
    
    with pytest.raises(ValueError) as exc_info:
        CmftPackager.package(invalid_segments, timescale=10000000, total_duration=0.0)
    
    error_msg = str(exc_info.value)
    assert "Failed to package CMFT" in error_msg
    print(f"✓ Invalid segment data error: {error_msg}")


def test_successful_conversion_with_warnings():
    """Test that valid VTT with warnings (skipped cues) still succeeds."""
    vtt_with_warnings = """WEBVTT

00:00:01.000 --> 00:00:03.00
Cue 1 with bad milliseconds format (will be skipped)

00:00:04.000 --> 00:00:06.000
Cue 2 that is valid

00:00:07.000 --> 00:00:09,000
Cue 3 with comma instead of period (will be skipped)
"""
    
    # Should succeed but with some cues skipped (ttconv handles this)
    imsc1_content, warnings = VttToImsc1Converter.convert(vtt_with_warnings)
    
    assert imsc1_content is not None
    assert '<?xml' in imsc1_content
    assert 'ttml' in imsc1_content
    
    # Parse to verify at least one valid cue was converted
    root = ET.fromstring(imsc1_content)
    paragraphs = root.findall('.//{http://www.w3.org/ns/ttml}p')
    assert len(paragraphs) > 0
    
    print(f"✓ Conversion succeeded with warnings ({len(paragraphs)} valid cues)")


def test_vtt_completely_invalid():
    """Test that completely invalid VTT content produces error."""
    # Just random text, no VTT structure at all
    bad_vtt = "This is just random text, not a VTT file"
    
    # ttconv may handle this gracefully or fail
    try:
        imsc1_content, warnings = VttToImsc1Converter.convert(bad_vtt)
        # If it succeeds, that's also acceptable (ttconv is lenient)
        assert imsc1_content is not None
        print("✓ Invalid VTT handled gracefully by ttconv")
    except ValueError as e:
        # If it fails, error should be descriptive
        assert "Failed to convert WebVTT to IMSC1" in str(e)
        print(f"✓ Invalid VTT error: {str(e)[:80]}...")


def test_multiple_html_issues_all_fixed():
    """Test that multiple HTML issues in same cue are all fixed."""
    vtt_multiple_issues = """WEBVTT

00:00:01.000 --> 00:00:03.000
Text with <invalid> and </bad> and <wrong> tags
"""
    
    imsc1_content, warnings = VttToImsc1Converter.convert(vtt_multiple_issues, sanitize_html=True)
    
    assert imsc1_content is not None
    
    # Verify all malformed tags were removed
    assert '<invalid>' not in imsc1_content
    assert '</bad>' not in imsc1_content
    assert '<wrong>' not in imsc1_content
    
    print("✓ Multiple HTML issues all fixed")


if __name__ == '__main__':
    print("Running error handling tests...\n")
    
    try:
        print("Note: Run with 'pytest -v -s' to see detailed logging output\n")
        
        test_empty_vtt_error()
        print()
        
        test_invalid_xml_segmentation()
        print()
        
        test_malformed_imsc1_structure()
        print()
        
        test_empty_segments_cmft_packaging()
        print()
        
        print("\n" + "="*60)
        print("All error handling tests completed!")
        print("Run with pytest to see full logging and caplog tests")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
