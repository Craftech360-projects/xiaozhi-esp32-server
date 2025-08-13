"""
TTS reporting functionality has been integrated into the ConnectionHandler class.

The reporting functionality includes:
1. Each connection object has its own reporting queue and processing thread
2. The lifecycle of the reporting thread is bound to the connection object
3. Use the ConnectionHandler.enqueue_tts_report method for reporting

For specific implementation, please refer to the relevant code in core/connection.py.
"""

import time

import opuslib_next

from config.manage_api_client import report as manage_report

TAG = __name__


def report(conn, type, text, opus_data, report_time):
    """Execute chat record reporting operation

    Args:
        conn: Connection object
        type: Report type, 1 for user, 2 for agent
        text: Synthesized text
        opus_data: opus audio data
        report_time: Report time
    """
    try:
        if opus_data:
            audio_data = opus_to_wav(conn, opus_data)
        else:
            audio_data = None
        # Execute reporting
        manage_report(
            mac_address=conn.device_id,
            session_id=conn.session_id,
            chat_type=type,
            content=text,
            audio=audio_data,
            report_time=report_time,
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Chat record reporting failed: {e}")


def opus_to_wav(conn, opus_data):
    """Convert Opus data to WAV format byte stream

    Args:
        output_dir: Output directory (parameter retained for interface compatibility)
        opus_data: opus audio data

    Returns:
        bytes: Audio data in WAV format
    """
    decoder = opuslib_next.Decoder(16000, 1)  # 16kHz, mono
    pcm_data = []

    for opus_packet in opus_data:
        try:
            pcm_frame = decoder.decode(opus_packet, 960)  # 960 samples = 60ms
            pcm_data.append(pcm_frame)
        except opuslib_next.OpusError as e:
            conn.logger.bind(tag=TAG).error(
                f"Opus decoding error: {e}", exc_info=True)

    if not pcm_data:
        raise ValueError("No valid PCM data")

    # Create WAV file header
    pcm_data_bytes = b"".join(pcm_data)
    num_samples = len(pcm_data_bytes) // 2  # 16-bit samples

    # WAV file header
    wav_header = bytearray()
    wav_header.extend(b"RIFF")  # ChunkID
    wav_header.extend(
        (36 + len(pcm_data_bytes)).to_bytes(4, "little"))  # ChunkSize
    wav_header.extend(b"WAVE")  # Format
    wav_header.extend(b"fmt ")  # Subchunk1ID
    wav_header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
    wav_header.extend((1).to_bytes(2, "little"))  # AudioFormat (PCM)
    wav_header.extend((1).to_bytes(2, "little"))  # NumChannels
    wav_header.extend((16000).to_bytes(4, "little"))  # SampleRate
    wav_header.extend((32000).to_bytes(4, "little"))  # ByteRate
    wav_header.extend((2).to_bytes(2, "little"))  # BlockAlign
    wav_header.extend((16).to_bytes(2, "little"))  # BitsPerSample
    wav_header.extend(b"data")  # Subchunk2ID
    wav_header.extend(len(pcm_data_bytes).to_bytes(
        4, "little"))  # Subchunk2Size

    # Return complete WAV data
    return bytes(wav_header) + pcm_data_bytes


def enqueue_tts_report(conn, text, opus_data):
    if not conn.read_config_from_api or conn.need_bind or not conn.report_tts_enable:
        return
    if conn.chat_history_conf == 0:
        return
    """Add TTS data to reporting queue

    Args:
        conn: Connection object
        text: Synthesized text
        opus_data: opus audio data
    """
    try:
        # Use the connection object's queue, pass in text and binary data instead of file path
        if conn.chat_history_conf == 2:
            conn.report_queue.put((2, text, opus_data, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"TTS data added to reporting queue: {conn.device_id}, audio size: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((2, text, None, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"TTS data added to reporting queue: {conn.device_id}, audio not reported"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(
            f"Failed to add TTS to reporting queue: {text}, {e}")


def enqueue_asr_report(conn, text, opus_data):
    if not conn.read_config_from_api or conn.need_bind or not conn.report_asr_enable:
        return
    if conn.chat_history_conf == 0:
        return
    """Add ASR data to reporting queue

    Args:
        conn: Connection object
        text: Synthesized text
        opus_data: opus audio data
    """
    try:
        # Use the connection object's queue, pass in text and binary data instead of file path
        if conn.chat_history_conf == 2:
            conn.report_queue.put((1, text, opus_data, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"ASR data added to reporting queue: {conn.device_id}, audio size: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((1, text, None, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"ASR data added to reporting queue: {conn.device_id}, audio not reported"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).debug(
            f"Failed to add ASR to reporting queue: {text}, {e}")
