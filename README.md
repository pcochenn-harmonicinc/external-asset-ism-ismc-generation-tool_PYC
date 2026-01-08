# ISM/ISMC manifests generation

harmonic_external_asset_ism_ismc_generation_tool is a command line tool to generate the ISM/ISMC manifest for the .mp4 files stored in Azure containers.
The tool parses .mp4 and .cmft files from an Azure container, generates .ism and .ismc manifests if they do not exist, and loads them into the Azure container. 

## Prerequisites
- Python 3.10+
- Python libs:
  - azure-core==1.29.4
  - azure-storage-blob==12.8.1
  - azure-identity==1.14.1
  - construct==2.8.8
  - pycountry==22.3.5
  - webvtt-py==0.5.1
  - ttconv==1.1.0

## Supported codecs
### Video codecs
- AVC
- HEVC
### Audio codecs
- AAC-LC
- AAC-HE (when it's compatible with AAC-LC and we interpret it as AAC-LC)
- E-AC3

## Supported formats:
# media formats:
- .mp4
- .mpi
- .ismv
- .isma
- .cmft

# text formats
- .ttml
- .vtt

## HowTo run
```
python3 main.py -connection_string=<Azure storage account's connection string> -container_name=<Azure container name>
```
or
```
python3 main.py
```
in case if the configuration file azure_config.json has been filled (the configuration file shall be situated in the same folder as the main.py file).
### azure_config.json
azure_config.json - configuration file may contain the following fields: connection_string, account_name, account_key, container_name:
```
{
  "connection_string": "DefaultEndpointsProtocol=https;AccountName=flametestextassetstorage;AccountKey=<key>;EndpointSuffix=core.windows.net",
  "account_name": "flametestextassetstorage",
  "account_key": "<key>",
  "container_name": "test2"
}
```
It's possible to set the `connection_string`  fileld or `account_name` and `account_key` .
If only the `account_name` and `account_key` fields are specified, the connection string is formed from them.
If all fields are set, only the `connection_string` field value is used. In this case the `account_name` and `account_key` fields are ignored.

Azure connection string can be found in Azure Portal → Storage container → Access keys → Connection string

## HowTo run with multithreading
```
python3 main.py -is_multithreading
```
Currently ISM/ISMC generation tool supports two modes: one-threaded and multi-threaded. Multi-threaded mode uses the maximum amount of threads your system can handle.

## HowTo run with local generation of ISM/ISMC (debug)
```
python3 main.py -local_copy
```

## Other Commands
```bash
python3 upload_asset.py     # unzip and upload an asset in Azure Blob
python3 remove_asset.py     # remove an asset from Azure Blob
pytest                      # run all unit tests
pytest tests/conversion_tests/  # run VTT conversion tests only
```

## Testing

The project includes comprehensive test coverage for VTT to CMFT conversion:

- **tests/conversion_tests/test_vtt_conversion.py**: 8 tests for VTT to IMSC1 conversion functionality
- **tests/conversion_tests/test_error_handling.py**: 11 tests for error handling and sanitization
- Total: 19 tests covering conversion pipeline, error cases, and HTML sanitization

Run tests with:
```bash
pytest tests/conversion_tests/ -v
```

## Key Directories

- `azure_client/` - Azure API management
- `file_processor/` - routing of file processing
- `media_data_parser/` - Processing of MP4 files
- `text_data_parser/` - Processing of text files (WebVTT and TTML)

## VTT to CMFT feature

A new feature has been added: converting WebVTT files found in the Azure container to CMFT files before manifest generation.

### Process Overview

This is a 6-step operation that runs automatically when `convert_webvtt=true`:

1. **Connect** to an Azure Blob container using configuration stored in file azure_config.json
2. **Detect** WebVTT files in the container based on their extension (.vtt)
3. **Convert** the WebVTT file to IMSC1 format using the `ttconv` library:
   - `time_format`: "clock_time"
   - `fps`: None
   - `xml:lang`: Extracted from VTT filename (e.g., "ara" for espn1_ARA.vtt)
4. **Segment** the IMSC1 using a fixed segment duration of 4 seconds (hard-coded, not derived from video segment duration)
5. **Package** the resulting IMSC1 in a single MP4/CMFT file:
   - Structure: ftyp + moov (with mdhd language encoding) + moof/mdat pairs (one per segment) + mfra
   - Language embedded in mdhd atom using 16-bit ISO 639-2/T encoding
6. **Upload** the resulting CMFT file to the Blob container

This process runs before the `generate_manifests()` call, so that CMFT files created by it will be processed during the manifest generation and appear in the generated manifests.

### Key Components

The VTT to CMFT conversion pipeline consists of four main components:

1. **VttToCmftConverter** (`vtt_to_cmft_converter.py`): Orchestrates the entire conversion process
2. **VttToImsc1Converter** (`vtt_to_imsc1_converter.py`): Converts WebVTT to IMSC1 format with HTML sanitization
3. **Imsc1Segmenter** (`imsc1_segmenter.py`): Segments IMSC1 content into fixed-duration chunks
4. **CmftPackager** (`cmft_packager.py`): Packages segmented IMSC1 into MP4/CMFT format

## Configuration Options

The application supports the following configuration options in `azure_config.json`:

### convert_webvtt (boolean, default: true)
Controls how WebVTT files are handled:
- **false**: VTT files are added to manifests as raw WebVTT (FourCC="WVTT")
- **true**: VTT files are converted to IMSC1, packaged as CMFT, and added to manifests as CMFT (FourCC="IMSC")
- **Note**: When set to `true`, manifests are automatically regenerated (overwrite_manifest is implicitly enabled) to include the converted CMFT files

### overwrite_manifest (boolean, default: false)
Controls manifest file overwriting behavior:
- **false**: Existing manifest files (.ism/.ismc) in the container are not regenerated
- **true**: Manifest files are regenerated even if they already exist in the container
- **Note**: This option is automatically set to `true` when `convert_webvtt=true`

## Implementation Details

### VTT to CMFT Conversion Pipeline

When `convert_webvtt=true`, the application performs a 5-step operation:

1. **Detection**: Identifies WebVTT files (.vtt) in the Azure Blob container
2. **IMSC1 Conversion**: Converts WebVTT to IMSC1 format using the `ttconv` library with parameters:
   - `time_format`: "clock_time"
   - `fps`: None
   - `xml:lang`: Extracted from VTT filename (e.g., "ara" for espn1_ARA.vtt)
3. **Segmentation**: Segments the IMSC1 file using a fixed segment duration (4 seconds)
4. **CMFT Packaging**: Packages segmented IMSC1 into an MP4/CMFT file using the `pymp4`library:
   - Structure: ftyp + moov (with mdhd language encoding) + moof/mdat pairs (one per segment)
   - Language embedded in mdhd atom using 16-bit ISO 639-2/T encoding
5. **Upload**: Uploads the generated CMFT file to the Azure Blob container

### Language Code Extraction

Language codes are extracted from filenames using flexible pattern matching:

**Pattern Recognition**:
- Uses regex `re.split(r'[_\-\.]', filename)` to split on underscores, hyphens, or dots
- Searches all filename segments for 3-letter ISO 639-2/T codes
- Position-independent: Works with `espn1_ARA.vtt`, `ARA_espn1.vtt`, or `espn1.ara.vtt`

**Extraction Points**:
- VTT files: `text_data_parser.py` extracts during initial processing
- CMFT files: `media_track_info_extractor.py` extracts when track metadata contains 'und'

**Fallback Strategy**:
- For CMFT files generated externally: Uses track metadata language (from mdhd atom)
- If track language is 'und' or missing: Falls back to filename extraction
- For VTT files: Always uses filename extraction (VTT format has no embedded language)

### Language Code Embedding (Three-Level Strategy)

Language codes are embedded at three levels to ensure proper signalization:

**Level 1: IMSC1 XML Syntax**
- The `xml:lang` attribute is set on the root `<tt>` element
- Example: `<tt xml:lang="ara">` for Arabic content
- Implementation: `vtt_to_imsc1_converter.py` sets the attribute after ttconv conversion

**Level 2: CMFT Track Metadata**
- Language is encoded in the `mdhd` atom of the CMFT track using 16-bit MP4 format
- Encoding: Each character uses 5 bits (a=1, b=2, ..., z=26)
- Examples: "ara" → 0x0641, "eng" → 0x15c7, "fre" → 0x1a45, "und" → 0x55c4
- Implementation: `cmft_packager.py` replaces hardcoded 'und' with extracted language code

**Level 3: Manifest Signalization**
- The `systemLanguage` attribute is added to text streams in ISM manifests
- Example: `<textstream src="espn1_ARA.cmft" systemLanguage="ara">`
- Implementation: `ism_generator.py` includes language in both text and media stream generation

### VTT File Handling Modes

**Mode 1: convert_webvtt = false**
- VTT files are processed as-is and added to manifests
- FourCC in manifest: "WVTT"
- Language code: Extracted from filename, added to `systemLanguage` attribute
- Use case: When clients support native WebVTT playback

**Mode 2: convert_webvtt = true** (default)
- VTT files are converted to CMFT during preprocessing
- VTT files are excluded from manifest generation (handled by `blob_data_handler.py`)
- Only generated CMFT files appear in manifests with FourCC "IMSC"
- Language code: Propagated through all three embedding levels
- Use case: For maximum compatibility with Smooth Streaming clients

### Modified Components

The following files were modified to implement these features:

**Configuration & Main Flow**:
- `azure_config.json`: Added `convert_webvtt` and `overwrite_manifest` options
- `main.py`: Conditional VTT conversion and manifest overwriting logic
- `azure_blob_service_client.py`: Added `overwrite` parameter to upload method

**VTT Conversion Pipeline**:
- `vtt_to_cmft_converter.py`: Orchestrates conversion, extracts language from filename
- `vtt_to_imsc1_converter.py`: Adds `xml:lang` attribute to IMSC1 root element
- `cmft_packager.py`: Encodes language in mdhd atom (16-bit ISO 639-2/T format)

**Language Extraction & Processing**:
- `text_data_parser/text_data_parser.py`: Extracts language from VTT filenames
- `text_data_parser/model/text_data_info.py`: Added `language` field
- `media_data_parser/media_track_info_extractor.py`: Extracts language from CMFT filenames (fallback)

**Manifest Generation**:
- `blob_data_handler.py`: Skips VTT files when `convert_webvtt=true` (early filtering in `__process_blob()`)
- `mss_server_manifest/ism_generator.py`: Includes `systemLanguage` and `trackName` param in text streams
- `mss_client_manifest/ismc_generator.py`: Includes track name in text stream indexes

**Supporting Models**:
- `text_data_parser/model/conversion_summary.py`: Contains `ConversionSummary`, `ManifestResult`, and `ProcessingSummary` classes for tracking and reporting processing results
- `mss_client_manifest/ismc_generator.py`: Includes track name in text stream indexes

### Track Naming Convention

Track names are automatically generated based on language codes using the `pycountry` library:

**For Audio and Text Tracks (CMFT)**:
- Valid language code → Full language name (e.g., "ara" → "Arabic", "eng" → "English", "fre" → "French")
- No valid language code or 'und' → fallback to "text_N" where N is the index in the track type
- Multiple tracks with same language → Numbered suffix (e.g., "English", "English1", "English2")

**For Video Tracks**:
- Standard naming: "video_0", "video_1", etc.

**Manifest Integration**:
- **ISM (Server Manifest)**: Track name added as `<param name="trackName" value="English" valuetype="data"/>` for both audio and text tracks
- **ISMC (Client Manifest)**: Track name used in StreamIndex `Name` attribute and URL pattern

**Implementation**:
- `media_data_parser.py`: Processes audio and CMFT text tracks in `__update_media_track_info_list()`
- `ism_generator.py`: Adds trackName param for both `__get_text_streams_from_media()` and `__get_text_streams_from_text()`
- `ismc_generator.py`: Processes VTT and TTML text tracks in `__get_text_stream_indexes_from_text_data_info_list()`
- All use `Common.get_language_3_code_and_name()` for consistent language resolution

### Movie Fragment Random Access (mfra) Box

CMFT files generated from VTT conversion include an **mfra** (Movie Fragment Random Access) box at the end of the file, following the ISO 14496-12:2022 standard. This box enables efficient random access and seeking within fragmented MP4 files.

**Structure**:
- **mfra** (MovieFragmentRandomAccessBox): Container box placed at the end of the CMFT file
  - **tfra** (TrackFragmentRandomAccessBox): Contains random access entries for the subtitle track
  - **mfro** (MovieFragmentRandomAccessOffsetBox): Contains the size of the enclosing mfra box (placed last)

**tfra Box Details**:
- FullBox with version 0 (32-bit time and offset fields)
- track_ID: 1 (subtitle track)
- One entry per segment containing:
  - **time**: Presentation time in media timescale units (not movie timescale)
  - **moof_offset**: Byte offset from start of file to the moof box for this segment
  - **traf_number**: Always 1 (one traf per moof)
  - **trun_number**: Always 1 (one trun per traf)
  - **sample_delta**: Always 1 (first sample in trun)

**mfro Box Details**:
- FullBox with version 0
- **parent_size**: Size of the enclosing mfra box in bytes
- Placed last in mfra box to enable backwards scanning from end of file

**Implementation**:
- `cmft_packager.py`: Creates mfra/tfra/mfro boxes in `__create_mfra_box()`, `__create_tfra_box()`, `__create_mfro_box()`
- Tracks moof offsets and presentation times during segment packaging
- Appends complete mfra box after all moof/mdat pairs

**Benefits**:
- Enables efficient seeking to specific timestamps
- Provides quick access to sync samples without parsing entire file
- Complies with ISO 14496-12 fragmented MP4 standard

## Error Handling

The VTT to CMFT conversion pipeline implements comprehensive error handling at each stage to ensure robust operation and provide clear diagnostics when issues occur.

### Error Detection and Reporting Strategy

**Three-Level Error Handling Approach**:

1. **Validation Errors**: Detected before processing begins (empty content, missing headers, invalid structure)
2. **Sanitization Fixes**: Non-fatal issues automatically corrected with detailed logging
3. **Fatal Errors**: Issues that prevent successful conversion with descriptive error messages

### VTT to IMSC1 Conversion Errors

**Input Validation**:
- **Empty VTT Content**: Detects and reports empty or whitespace-only VTT content before processing
- **Error Message**: "VTT content is empty or contains only whitespace"

**HTML Sanitization** (when `sanitize_html=True`, default):
- **Automatic Fix**: Removes malformed HTML tags while preserving valid VTT tags (b, i, u, ruby, rt, v, c, lang)
- **Logging**: Reports each fixed issue with cue number and specific tags removed
- **Example Log**:
  ```
  Sanitization fixed 2 issue(s):
    - Cue 1: Removed invalid closing tags: </bad>
    - Cue 2: Removed invalid opening tags: <invalid>
  ```
- **No Issues Found**: Logs "No HTML sanitization issues found" when VTT is clean

**Conversion Errors**:
- **AttributeError**: Malformed VTT structure or missing required elements
  - Message: "Malformed VTT structure - missing required elements or invalid format"
  - Advice: "Check that the VTT file has proper WEBVTT header and valid cue structure"
  
- **TypeError**: Invalid cue text or HTML parsing issues
  - Message: "Invalid VTT content - malformed HTML tags or cue text"
  - Advice: "Consider enabling HTML sanitization (sanitize_html=True)" (when disabled)
  
- **ValueError**: Invalid timing formats or other validation errors
  - Message: "VTT validation error - invalid timing or format"
  - Advice: "Check that all timestamps follow HH:MM:SS.mmm format with proper '-->' separator"
  
- **UnicodeDecodeError**: Character encoding problems
  - Message: "VTT file encoding error"
  - Advice: "Ensure the VTT file is UTF-8 encoded"

### IMSC1 Segmentation Errors

**XML Parsing Errors**:
- **ET.ParseError**: Invalid XML syntax in IMSC1 content
  - Message: "Failed to parse IMSC1 XML: {details}"
  - Advice: "Check that the IMSC1 content is valid XML"

**Structure Validation**:
- **Missing body element**: IMSC1 missing required `<body>` element
  - Message: "No body element found in IMSC1 content"
  
- **Missing div element**: IMSC1 missing required `<div>` element inside body
  - Message: "No div element found in IMSC1 content"

**Unexpected Errors**:
- Logs error type, segment duration, and other diagnostic information
- Message format: "Unexpected error segmenting IMSC1 ({ErrorType}): {details}"

### CMFT Packaging Errors

**Data Validation**:
- **ValueError**: Invalid segment data or structure
  - Message: "CMFT packaging validation error: {details}"
  
- **struct.error**: Binary data packing issues
  - Message: "CMFT binary data packing error: {details}"
  - Diagnostic: Logs segment count for troubleshooting

**Unexpected Errors**:
- Logs error type, segment count, timescale, and duration
- Message format: "Unexpected error packaging CMFT ({ErrorType}): {details}"

### Error Handling Best Practices

**For Pipeline Integration**:
1. All conversion functions raise `ValueError` with descriptive messages for consistency
2. Error messages include specific details to aid troubleshooting
3. Log messages provide actionable advice for resolution
4. Sanitization operates transparently, logging all automatic fixes

**For Testing**:
- Comprehensive error handling tests in `tests/conversion_tests/test_error_handling.py`
- Tests cover all error types: empty content, malformed HTML, invalid XML, invalid structure
- Tests verify both error messages and successful sanitization
- 11 dedicated error handling tests ensure robust error detection

**For Developers**:
- Enable HTML sanitization (`sanitize_html=True`) for user-generated VTT files
- Monitor logs for sanitization reports to identify recurring data quality issues
- All errors include enough context for debugging without inspecting source code
- Error messages distinguish between recoverable (sanitized) and fatal errors

### Conversion Summary

After processing completes, a comprehensive summary is displayed showing both VTT conversion and manifest generation results.

The summary provides:
- VTT conversion statistics (successful/total)
- List of files with sanitization warnings (automatically fixed HTML issues)
- List of failed files with specific error reasons
- Manifest generation status (created or skipped)
- Appears at the end of processing, after both VTT conversion and manifest generation
