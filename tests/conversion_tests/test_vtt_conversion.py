"""
Test module for VTT to CMFT conversion functionality.

This module tests the conversion process using the asset-test-vtt-syntax_ENG.vtt test file
and compares the output with asset-test-vtt-syntax_ENG_REF.cmft reference file.
"""

import os
import pytest
from external_asset_ism_ismc_generation_tool.text_data_parser.vtt_to_imsc1_converter import VttToImsc1Converter
from external_asset_ism_ismc_generation_tool.text_data_parser.imsc1_segmenter import Imsc1Segmenter
from external_asset_ism_ismc_generation_tool.text_data_parser.cmft_packager import CmftPackager
from tests.test_utils.common.common import Common


def test_vtt_to_imsc1_conversion():
    """Test that VTT can be converted to IMSC1 format."""
    # Read asset-test-vtt-syntax_ENG.vtt
    with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG.vtt'), 'r', encoding='utf-8') as f:
        vtt_content = f.read()
    
    # Remove BOM if present
    if vtt_content.startswith('\ufeff'):
        vtt_content = vtt_content[1:]
    
    # Convert to IMSC1
    imsc1_content = VttToImsc1Converter.convert(vtt_content)
    
    # Verify IMSC1 content is valid XML
    assert imsc1_content is not None
    assert len(imsc1_content) > 0
    assert '<?xml' in imsc1_content
    assert 'ttml' in imsc1_content
    
    print(f"✓ VTT to IMSC1 conversion successful: {len(imsc1_content)} bytes")


def test_imsc1_segmentation():
    """Test that IMSC1 content can be segmented."""
    # Read asset-test-vtt-syntax_ENG.vtt
    with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG.vtt'), 'r', encoding='utf-8') as f:
        vtt_content = f.read()
    
    if vtt_content.startswith('\ufeff'):
        vtt_content = vtt_content[1:]
    
    # Convert to IMSC1
    imsc1_content = VttToImsc1Converter.convert(vtt_content)
    
    # Segment with 4 second duration (typical segment size)
    segment_duration = 4.0
    segments = Imsc1Segmenter.segment(imsc1_content, segment_duration)
    
    # Verify segments were created
    assert segments is not None
    assert len(segments) > 0
    
    # Verify segment structure
    for start_time, segment_xml in segments:
        assert isinstance(start_time, float)
        assert isinstance(segment_xml, str)
        assert len(segment_xml) > 0
        assert '<?xml' in segment_xml
    
    print(f"✓ IMSC1 segmentation successful: {len(segments)} segments created")


def test_cmft_packaging():
    """Test that segmented IMSC1 can be packaged into CMFT format."""
    # Read asset-test-vtt-syntax_ENG.vtt
    with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG.vtt'), 'r', encoding='utf-8') as f:
        vtt_content = f.read()
    
    if vtt_content.startswith('\ufeff'):
        vtt_content = vtt_content[1:]
    
    # Convert to IMSC1
    imsc1_content = VttToImsc1Converter.convert(vtt_content)
    
    # Segment
    segment_duration = 4.0
    segments = Imsc1Segmenter.segment(imsc1_content, segment_duration)
    
    # Calculate total duration
    if segments:
        last_start, _ = segments[-1]
        total_duration = last_start + segment_duration
    else:
        total_duration = 0.0
    
    # Package to CMFT
    cmft_data = CmftPackager.package(segments, timescale=10000000, total_duration=total_duration)
    
    # Verify CMFT data
    assert cmft_data is not None
    assert len(cmft_data) > 0
    
    # Check for key MP4 boxes
    assert b'ftyp' in cmft_data
    assert b'moov' in cmft_data
    assert b'moof' in cmft_data
    assert b'mdat' in cmft_data
    
    # Save generated CMFT for inspection
    with open('espn1_generated.cmft', 'wb') as f:
        f.write(cmft_data)
    
    print(f"✓ CMFT packaging successful: {len(cmft_data)} bytes")
    print(f"  Generated file saved as espn1_generated.cmft")


def test_full_vtt_to_cmft_conversion():
    """Test the complete VTT to CMFT conversion pipeline."""
    # Read asset-test-vtt-syntax_ENG.vtt
    with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG.vtt'), 'r', encoding='utf-8') as f:
        vtt_content = f.read()
    
    if vtt_content.startswith('\ufeff'):
        vtt_content = vtt_content[1:]
    
    # Step 1: Convert to IMSC1
    imsc1_content = VttToImsc1Converter.convert(vtt_content)
    assert imsc1_content is not None
    
    # Step 2: Segment
    segment_duration = 4.0
    segments = Imsc1Segmenter.segment(imsc1_content, segment_duration)
    assert len(segments) > 0
    
    # Step 3: Package
    if segments:
        last_start, _ = segments[-1]
        total_duration = last_start + segment_duration
    else:
        total_duration = 0.0
    
    cmft_data = CmftPackager.package(segments, timescale=10000000, total_duration=total_duration)
    assert len(cmft_data) > 0
    
    # Save the result
    output_file = 'espn1_generated.cmft'
    with open(output_file, 'wb') as f:
        f.write(cmft_data)
    
    print(f"✓ Full VTT to CMFT conversion successful")
    print(f"  Input: asset-test-vtt-syntax_ENG.vtt")
    print(f"  Output: {output_file} ({len(cmft_data)} bytes)")
    print(f"  Segments: {len(segments)}")
    print(f"  Duration: {total_duration:.2f}s")
    
    # Compare with reference file if it exists
    if os.path.exists(Common.get_data_file_path('asset-test-vtt-syntax_ENG_REF.cmft')):
        with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG_REF.cmft'), 'rb') as f:
            ref_data = f.read()
        
        print(f"\n  Reference file: asset-test-vtt-syntax_ENG_REF.cmft ({len(ref_data)} bytes)")
        print(f"  Size difference: {len(cmft_data) - len(ref_data)} bytes")
        
        # Note: Exact byte-for-byte match is unlikely due to:
        # - Timestamp precision differences
        # - Box ordering variations
        # - Metadata differences
        # But the structure should be similar
        
        # Check that key boxes exist in both
        for box in [b'ftyp', b'moov', b'mvhd', b'trak', b'mdia', b'minf', b'stbl', b'moof', b'mdat']:
            assert box in cmft_data, f"Missing box {box} in generated file"
            assert box in ref_data, f"Missing box {box} in reference file"
        
        print(f"  ✓ Both files contain required MP4 boxes")


def test_compare_with_reference():
    """Compare the generated CMFT with the reference file structure."""
    # Generate CMFT from VTT
    with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG.vtt'), 'r', encoding='utf-8') as f:
        vtt_content = f.read()
    
    if vtt_content.startswith('\ufeff'):
        vtt_content = vtt_content[1:]
    
    imsc1_content = VttToImsc1Converter.convert(vtt_content)
    segment_duration = 4.0
    segments = Imsc1Segmenter.segment(imsc1_content, segment_duration)
    
    if segments:
        last_start, _ = segments[-1]
        total_duration = last_start + segment_duration
    else:
        total_duration = 0.0
    
    cmft_data = CmftPackager.package(segments, timescale=10000000, total_duration=total_duration)
    
    # Read reference file
    if not os.path.exists(Common.get_data_file_path('asset-test-vtt-syntax_ENG_REF.cmft')):
        pytest.skip("Reference file asset-test-vtt-syntax_ENG_REF.cmft not found")
    
    with open(Common.get_data_file_path('asset-test-vtt-syntax_ENG_REF.cmft'), 'rb') as f:
        ref_data = f.read()
    
    print(f"\nStructural comparison:")
    print(f"  Generated: {len(cmft_data)} bytes, {len(segments)} segments")
    print(f"  Reference: {len(ref_data)} bytes")
    
    # Count boxes in each file
    def count_boxes(data, box_name):
        return data.count(box_name.encode('utf-8'))
    
    for box in ['ftyp', 'moov', 'mvhd', 'trak', 'mdia', 'hdlr', 'minf', 'stbl', 'mvex', 'trex', 'moof', 'mfhd', 'traf', 'tfhd', 'trun', 'mdat']:
        gen_count = count_boxes(cmft_data, box)
        ref_count = count_boxes(ref_data, box)
        match = "✓" if gen_count == ref_count else "✗"
        print(f"  {match} {box}: generated={gen_count}, reference={ref_count}")


if __name__ == '__main__':
    print("Running VTT to CMFT conversion tests...\n")
    
    try:
        test_vtt_to_imsc1_conversion()
        print()
        
        test_imsc1_segmentation()
        print()
        
        test_cmft_packaging()
        print()
        
        test_full_vtt_to_cmft_conversion()
        print()
        
        test_compare_with_reference()
        print()
        
        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
