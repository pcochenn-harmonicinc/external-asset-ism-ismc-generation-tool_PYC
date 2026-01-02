import struct
from typing import List, Tuple
from uuid import UUID

from external_asset_ism_ismc_generation_tool.common.logger.i_logger import ILogger
from external_asset_ism_ismc_generation_tool.common.logger.logger import Logger


class CmftPackager:
    """Packages segmented IMSC1 content into MP4/CMFT format."""
    
    __logger: ILogger = Logger("CmftPackager")

    @classmethod
    def redefine_logger(cls, logger: ILogger):
        cls.__logger = logger

    @staticmethod
    def package(segments: List[Tuple[float, str]], timescale: int = 10000000, total_duration: float = 0.0, language_code: str = 'und') -> bytes:
        """
        Package segmented IMSC1 content into CMFT format.
        
        Args:
            segments: List of tuples (start_time, imsc1_xml_string)
            timescale: Timescale for the track (default: 10000000 for 10MHz)
            total_duration: Total duration in seconds
            language_code: ISO 639-2/T 3-letter language code (default: 'und')
            
        Returns:
            Bytes containing the complete CMFT file
        """
        CmftPackager.__logger.info(f"Packaging {len(segments)} segments into CMFT")
        
        try:
            # Build the CMFT structure: ftyp + moov + (moof + mdat) for each segment + mfra
            cmft_data = bytearray()
            
            # 1. Create ftyp box
            ftyp_box = CmftPackager.__create_ftyp_box()
            cmft_data.extend(ftyp_box)
            
            # 2. Create moov box
            if not total_duration and segments:
                # Calculate from last segment
                last_start, last_xml = segments[-1]
                # Estimate duration from XML (simple approach)
                total_duration = last_start + 10  # Add some buffer
            
            moov_box = CmftPackager.__create_moov_box(timescale, total_duration, language_code)
            cmft_data.extend(moov_box)
            
            # 3. Create moof + mdat pairs for each segment and track random access info
            moof_offsets = []  # Track the file offset for each moof
            segment_times = []  # Track presentation time for each segment
            
            for idx, (start_time, imsc1_xml) in enumerate(segments):
                sequence_number = idx + 1
                
                # Record the offset of this moof box
                moof_offset = len(cmft_data)
                moof_offsets.append(moof_offset)
                
                # Convert start time to timescale units
                presentation_time = int(start_time * timescale)
                segment_times.append(presentation_time)
                
                # Convert XML to bytes
                xml_bytes = imsc1_xml.encode('utf-8')
                
                # Calculate duration in timescale units
                if idx < len(segments) - 1:
                    next_start, _ = segments[idx + 1]
                    duration_seconds = next_start - start_time
                else:
                    duration_seconds = total_duration - start_time
                
                duration_timescale = int(duration_seconds * timescale)
                
                # Create moof box
                moof_box = CmftPackager.__create_moof_box(
                    sequence_number,
                    duration_timescale,
                    len(xml_bytes)
                )
                cmft_data.extend(moof_box)
                
                # Create mdat box
                mdat_box = CmftPackager.__create_mdat_box(xml_bytes)
                cmft_data.extend(mdat_box)
            
            # 4. Create mfra box with random access information
            mfra_box = CmftPackager.__create_mfra_box(moof_offsets, segment_times)
            cmft_data.extend(mfra_box)
            
            CmftPackager.__logger.info(f"Successfully packaged CMFT: {len(cmft_data)} bytes")
            return bytes(cmft_data)
            
        except Exception as e:
            CmftPackager.__logger.error(f"Error packaging CMFT: {e}")
            raise ValueError(f"Failed to package CMFT: {e}")

    @staticmethod
    def __create_ftyp_box() -> bytes:
        """Create the ftyp (file type) box."""
        # ftyp box: major brand = iso6, minor version = 1, compatible brands = iso6
        major_brand = b'iso6'
        minor_version = 1
        compatible_brands = [b'iso6']
        
        box_data = b'ftyp' + major_brand + struct.pack('>I', minor_version)
        for brand in compatible_brands:
            box_data += brand
        
        # Add size at the beginning
        box_size = len(box_data) + 4
        return struct.pack('>I', box_size) + box_data

    @staticmethod
    def __create_moov_box(timescale: int, duration: float, language_code: str = 'und') -> bytes:
        """Create the moov (movie) box with subtitle track definition."""
        # Convert duration to timescale units
        duration_timescale = int(duration * timescale)
        creation_time = 0xe0daa988  # Fixed value from reference
        modification_time = 0xe0daa988
        
        # Build mvhd box
        mvhd_data = b'mvhd'
        mvhd_data += struct.pack('>B', 1)  # version 1
        mvhd_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        mvhd_data += struct.pack('>Q', creation_time)  # creation_time
        mvhd_data += struct.pack('>Q', modification_time)  # modification_time
        mvhd_data += struct.pack('>I', timescale)  # timescale
        mvhd_data += struct.pack('>Q', duration_timescale)  # duration
        mvhd_data += struct.pack('>I', 0x00010000)  # rate = 1.0
        mvhd_data += struct.pack('>H', 0x0100)  # volume = 1.0
        mvhd_data += b'\x00' * 10  # reserved
        # Unity matrix
        for val in [0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000]:
            mvhd_data += struct.pack('>I', val)
        mvhd_data += b'\x00' * 24  # pre_defined
        mvhd_data += struct.pack('>I', 2)  # next_track_ID
        
        mvhd_box = struct.pack('>I', len(mvhd_data) + 4) + mvhd_data
        
        # Build mvex box (movie extends)
        # trex (track extends) box
        trex_data = b'trex'
        trex_data += struct.pack('>B', 0)  # version
        trex_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        trex_data += struct.pack('>I', 1)  # track_ID
        trex_data += struct.pack('>I', 1)  # default_sample_description_index
        trex_data += struct.pack('>I', 0)  # default_sample_duration
        trex_data += struct.pack('>I', 0)  # default_sample_size
        trex_data += struct.pack('>I', 0)  # default_sample_flags
        
        trex_box = struct.pack('>I', len(trex_data) + 4) + trex_data
        
        mvex_data = b'mvex' + trex_box
        mvex_box = struct.pack('>I', len(mvex_data) + 4) + mvex_data
        
        # Build trak box (track)
        trak_box = CmftPackager.__create_trak_box(timescale, duration_timescale, creation_time, modification_time, language_code)
        
        # Combine into moov box
        moov_data = b'moov' + mvhd_box + mvex_box + trak_box
        return struct.pack('>I', len(moov_data) + 4) + moov_data

    @staticmethod
    def __create_trak_box(timescale: int, duration: int, creation_time: int, modification_time: int, language_code: str = 'und') -> bytes:
        """Create the trak (track) box for subtitle track."""
        # tkhd (track header) box
        tkhd_data = b'tkhd'
        tkhd_data += struct.pack('>B', 1)  # version 1
        tkhd_data += struct.pack('>I', 0x000003)[1:]  # flags: track enabled (3 bytes)
        tkhd_data += struct.pack('>Q', creation_time)
        tkhd_data += struct.pack('>Q', modification_time)
        tkhd_data += struct.pack('>I', 1)  # track_ID
        tkhd_data += struct.pack('>I', 0)  # reserved
        tkhd_data += struct.pack('>Q', duration)
        tkhd_data += b'\x00' * 8  # reserved
        tkhd_data += struct.pack('>H', 0)  # layer
        tkhd_data += struct.pack('>H', 0)  # alternate_group
        tkhd_data += struct.pack('>H', 0)  # volume
        tkhd_data += struct.pack('>H', 0)  # reserved
        # Unity matrix
        for val in [0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000]:
            tkhd_data += struct.pack('>I', val)
        tkhd_data += struct.pack('>I', 0)  # width
        tkhd_data += struct.pack('>I', 0)  # height
        
        tkhd_box = struct.pack('>I', len(tkhd_data) + 4) + tkhd_data
        
        # mdia (media) box
        mdia_box = CmftPackager.__create_mdia_box(timescale, duration, creation_time, modification_time, language_code)
        
        # Combine into trak box
        trak_data = b'trak' + tkhd_box + mdia_box
        return struct.pack('>I', len(trak_data) + 4) + trak_data

    @staticmethod
    def __create_mdia_box(timescale: int, duration: int, creation_time: int, modification_time: int, language_code: str = 'und') -> bytes:
        """Create the mdia (media) box."""
        # mdhd (media header) box
        mdhd_data = b'mdhd'
        mdhd_data += struct.pack('>B', 1)  # version 1
        mdhd_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        mdhd_data += struct.pack('>Q', creation_time)
        mdhd_data += struct.pack('>Q', modification_time)
        mdhd_data += struct.pack('>I', timescale)
        mdhd_data += struct.pack('>Q', duration)
        mdhd_data += struct.pack('>H', CmftPackager.__encode_language(language_code))  # language
        mdhd_data += struct.pack('>H', 0)  # pre_defined
        
        mdhd_box = struct.pack('>I', len(mdhd_data) + 4) + mdhd_data
        
        # hdlr (handler) box
        hdlr_data = b'hdlr'
        hdlr_data += struct.pack('>I', 0)  # version + flags
        hdlr_data += struct.pack('>I', 0)  # pre_defined
        hdlr_data += b'subt'  # handler_type = subtitle
        hdlr_data += b'\x00' * 12  # reserved
        hdlr_data += b'subt\x00'  # name
        
        hdlr_box = struct.pack('>I', len(hdlr_data) + 4) + hdlr_data
        
        # minf (media information) box
        minf_box = CmftPackager.__create_minf_box()
        
        # Combine into mdia box
        mdia_data = b'mdia' + mdhd_box + hdlr_box + minf_box
        return struct.pack('>I', len(mdia_data) + 4) + mdia_data

    @staticmethod
    def __create_minf_box() -> bytes:
        """Create the minf (media information) box."""
        # sthd (subtitle media header) box
        sthd_data = b'sthd'
        sthd_data += struct.pack('>I', 0)  # version + flags
        
        sthd_box = struct.pack('>I', len(sthd_data) + 4) + sthd_data
        
        # dinf (data information) box
        dref_data = b'dref'
        dref_data += struct.pack('>I', 0)  # version + flags
        dref_data += struct.pack('>I', 1)  # entry_count
        # url box
        url_data = b'url '
        url_data += struct.pack('>I', 1)  # version + flags (self-contained)
        url_box = struct.pack('>I', len(url_data) + 4) + url_data
        dref_data += url_box
        
        dref_box = struct.pack('>I', len(dref_data) + 4) + dref_data
        dinf_data = b'dinf' + dref_box
        dinf_box = struct.pack('>I', len(dinf_data) + 4) + dinf_data
        
        # stbl (sample table) box
        stbl_box = CmftPackager.__create_stbl_box()
        
        # Combine into minf box
        minf_data = b'minf' + sthd_box + dinf_box + stbl_box
        return struct.pack('>I', len(minf_data) + 4) + minf_data

    @staticmethod
    def __create_stbl_box() -> bytes:
        """Create the stbl (sample table) box."""
        # stsd (sample description) box
        stsd_data = b'stsd'
        stsd_data += struct.pack('>I', 0)  # version + flags
        stsd_data += struct.pack('>I', 1)  # entry_count
        
        # stpp (subtitle sample entry) box
        stpp_data = b'stpp'
        stpp_data += b'\x00' * 6  # reserved
        stpp_data += struct.pack('>H', 1)  # data_reference_index
        stpp_data += b'http://www.w3.org/ns/ttml\x00'  # namespace
        stpp_data += b'\x00' * 2  # reserved
        # mime box
        mime_data = b'mime'
        mime_data += struct.pack('>I', 0)  # version + flags
        mime_data += b'application/ttml+xml;codecs=im1t\x00'
        mime_box = struct.pack('>I', len(mime_data) + 4) + mime_data
        stpp_data += mime_box
        
        stpp_box = struct.pack('>I', len(stpp_data) + 4) + stpp_data
        stsd_data += stpp_box
        
        stsd_box = struct.pack('>I', len(stsd_data) + 4) + stsd_data
        
        # Empty boxes
        stts_box = struct.pack('>I', 16) + b'stts' + struct.pack('>I', 0) + struct.pack('>I', 0)
        stsc_box = struct.pack('>I', 16) + b'stsc' + struct.pack('>I', 0) + struct.pack('>I', 0)
        stsz_box = struct.pack('>I', 20) + b'stsz' + struct.pack('>I', 0) + struct.pack('>I', 0) + struct.pack('>I', 0)
        stco_box = struct.pack('>I', 16) + b'stco' + struct.pack('>I', 0) + struct.pack('>I', 0)
        
        # Combine into stbl box
        stbl_data = b'stbl' + stsd_box + stts_box + stsc_box + stsz_box + stco_box
        return struct.pack('>I', len(stbl_data) + 4) + stbl_data

    @staticmethod
    def __create_moof_box(sequence_number: int, duration: int, sample_size: int) -> bytes:
        """Create a moof (movie fragment) box."""
        # mfhd (movie fragment header) box
        mfhd_data = b'mfhd'
        mfhd_data += struct.pack('>I', 0)  # version + flags
        mfhd_data += struct.pack('>I', sequence_number)
        
        mfhd_box = struct.pack('>I', len(mfhd_data) + 4) + mfhd_data
        
        # traf (track fragment) box
        # tfhd (track fragment header) box
        tfhd_data = b'tfhd'
        tfhd_data += struct.pack('>B', 0)  # version
        tfhd_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        tfhd_data += struct.pack('>I', 1)  # track_ID
        
        tfhd_box = struct.pack('>I', len(tfhd_data) + 4) + tfhd_data
        
        # uuid box (Microsoft-specific timing info)
        uuid_bytes = UUID('6d1d9b05-42d5-44e6-80e2-141daff757b2').bytes
        uuid_data = b'uuid' + uuid_bytes
        uuid_data += struct.pack('>B', 1)  # version
        uuid_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        uuid_data += struct.pack('>Q', 0)  # track_ID
        uuid_data += struct.pack('>Q', duration)  # fragment_duration
        
        uuid_box = struct.pack('>I', len(uuid_data) + 4) + uuid_data
        
        # trun (track run) box
        trun_data = b'trun'
        trun_data += struct.pack('>B', 0)  # version
        # flags: data_offset_present (0x000001) + sample_duration_present (0x000100) + sample_size_present (0x000200)
        trun_data += struct.pack('>I', 0x000301)[1:]  # flags (3 bytes)
        trun_data += struct.pack('>I', 1)  # sample_count
        # Calculate data_offset: moof size + mdat header (8 bytes)
        moof_size_estimate = 120  # Approximate size
        data_offset = moof_size_estimate + 8
        trun_data += struct.pack('>I', data_offset)  # data_offset
        trun_data += struct.pack('>I', duration)  # sample_duration
        trun_data += struct.pack('>I', sample_size)  # sample_size
        
        trun_box = struct.pack('>I', len(trun_data) + 4) + trun_data
        
        # Combine into traf box
        traf_data = b'traf' + tfhd_box + uuid_box + trun_box
        traf_box = struct.pack('>I', len(traf_data) + 4) + traf_data
        
        # Combine into moof box
        moof_data = b'moof' + mfhd_box + traf_box
        return struct.pack('>I', len(moof_data) + 4) + moof_data

    @staticmethod
    def __create_mdat_box(data: bytes) -> bytes:
        """Create an mdat (media data) box."""
        mdat_data = b'mdat' + data
        return struct.pack('>I', len(mdat_data) + 4) + mdat_data

    @staticmethod
    def __encode_language(language_code: str) -> int:
        """
        Encode ISO 639-2/T language code to MP4 format.
        Each character is stored as 5 bits, with 'a' = 1, 'b' = 2, ..., 'z' = 26.
        
        Args:
            language_code: 3-letter ISO 639-2/T code (e.g., 'eng', 'ara', 'fre')
            
        Returns:
            16-bit integer representation
        """
        if len(language_code) != 3:
            language_code = 'und'
        
        language_code = language_code.lower()
        
        # Encode each character as 5 bits: a=1, b=2, ..., z=26
        encoded = 0
        for i, char in enumerate(language_code):
            if 'a' <= char <= 'z':
                value = ord(char) - ord('a') + 1
            else:
                value = 0  # Invalid character
            encoded |= (value << (10 - i * 5))
        
        return encoded

    @staticmethod
    def __create_mfra_box(moof_offsets: List[int], segment_times: List[int]) -> bytes:
        """
        Create the mfra (movie fragment random access) box.
        
        Args:
            moof_offsets: List of file offsets for each moof box
            segment_times: List of presentation times for each segment (in timescale units)
            
        Returns:
            Bytes containing the complete mfra box with tfra and mfro
        """
        # Create tfra box for track 1 (subtitle track)
        tfra_box = CmftPackager.__create_tfra_box(moof_offsets, segment_times)
        
        # Calculate mfra box size (will include tfra + mfro)
        # mfra header: 8 bytes (size + 'mfra')
        # tfra box: calculated
        # mfro box: 16 bytes (8 header + 8 version/flags/parent_size)
        mfra_size = 8 + len(tfra_box) + 16
        
        # Create mfro box
        mfro_box = CmftPackager.__create_mfro_box(mfra_size)
        
        # Assemble mfra box
        mfra_data = b'mfra' + tfra_box + mfro_box
        return struct.pack('>I', len(mfra_data) + 4) + mfra_data

    @staticmethod
    def __create_tfra_box(moof_offsets: List[int], segment_times: List[int]) -> bytes:
        """
        Create the tfra (track fragment random access) box.
        
        Args:
            moof_offsets: List of file offsets for each moof box
            segment_times: List of presentation times for each segment (in timescale units)
            
        Returns:
            Bytes containing the complete tfra box
        """
        # tfra is a FullBox with version and flags
        tfra_data = b'tfra'
        tfra_data += struct.pack('>B', 0)  # version 0 (32-bit time and offset)
        tfra_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        
        # track_ID = 1 (our subtitle track)
        tfra_data += struct.pack('>I', 1)
        
        # reserved (26 bits) + length_size fields (2 bits each for traf, trun, sample)
        # length_size_of_traf_num = 0 (means 1 byte)
        # length_size_of_trun_num = 0 (means 1 byte)
        # length_size_of_sample_num = 0 (means 1 byte)
        # Format: 26 bits reserved + 2 bits traf + 2 bits trun + 2 bits sample = 32 bits total
        reserved_and_lengths = (0 << 6) | (0 << 4) | (0 << 2) | 0
        tfra_data += struct.pack('>I', reserved_and_lengths)
        
        # number_of_entry
        number_of_entries = len(moof_offsets)
        tfra_data += struct.pack('>I', number_of_entries)
        
        # Add entries for each segment
        for i in range(number_of_entries):
            # time (32-bit in version 0)
            tfra_data += struct.pack('>I', segment_times[i])
            
            # moof_offset (32-bit in version 0)
            tfra_data += struct.pack('>I', moof_offsets[i])
            
            # traf_number (1 byte, since length_size_of_traf_num = 0)
            # We have only one traf per moof, so always 1
            tfra_data += struct.pack('>B', 1)
            
            # trun_number (1 byte, since length_size_of_trun_num = 0)
            # We have only one trun per traf, so always 1
            tfra_data += struct.pack('>B', 1)
            
            # sample_delta (1 byte, since length_size_of_sample_num = 0)
            # sample_delta = 1 + desired_sample - first_sample_in_trun
            # Since we have one sample per trun starting at 1, delta = 1 + 1 - 1 = 1
            tfra_data += struct.pack('>B', 1)
        
        # Return with size prefix
        return struct.pack('>I', len(tfra_data) + 4) + tfra_data

    @staticmethod
    def __create_mfro_box(parent_size: int) -> bytes:
        """
        Create the mfro (movie fragment random access offset) box.
        
        Args:
            parent_size: Size of the enclosing mfra box (in bytes)
            
        Returns:
            Bytes containing the complete mfro box
        """
        # mfro is a FullBox with version and flags
        mfro_data = b'mfro'
        mfro_data += struct.pack('>B', 0)  # version 0
        mfro_data += struct.pack('>I', 0)[1:]  # flags (3 bytes)
        
        # parent_size (32-bit unsigned int)
        mfro_data += struct.pack('>I', parent_size)
        
        # Return with size prefix
        return struct.pack('>I', len(mfro_data) + 4) + mfro_data
