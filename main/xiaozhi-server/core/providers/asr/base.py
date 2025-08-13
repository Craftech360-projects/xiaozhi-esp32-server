import os
import wave
import copy
import uuid
import queue
import asyncio
import traceback
import threading
import opuslib_next
from abc import ABC, abstractmethod
from config.logger import setup_logging
from typing import Optional, Tuple, List
from core.handle.receiveAudioHandle import startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.utils.util import remove_punctuation_and_length
from core.handle.receiveAudioHandle import handleAudioMessage

TAG = __name__
logger = setup_logging()


class ASRProviderBase(ABC):
    def __init__(self):
        pass

    # Open audio channels
    # Default is non-streaming processing
    # Streaming processing should be overridden in subclasses
    async def open_audio_channels(self, conn):
        # TTS processing thread
        conn.asr_priority_thread = threading.Thread(
            target=self.asr_text_priority_thread, args=(conn,), daemon=True
        )
        conn.asr_priority_thread.start()

    # Sequential ASR audio processing
    def asr_text_priority_thread(self, conn):
        while not conn.stop_event.is_set():
            try:
                message = conn.asr_audio_queue.get(timeout=1)
                future = asyncio.run_coroutine_threadsafe(
                    handleAudioMessage(conn, message),
                    conn.loop,
                )
                future.result()
            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Failed to process ASR text: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    # Receive audio
    # Default is non-streaming processing
    # Streaming processing should be overridden in subclasses
    async def receive_audio(self, conn, audio, audio_have_voice):
        if conn.client_listen_mode == "auto" or conn.client_listen_mode == "realtime":
            have_voice = audio_have_voice
        else:
            have_voice = conn.client_have_voice

        # If current frame has no voice and segment has no voice, discard the audio
        conn.asr_audio.append(audio)
        if have_voice == False and conn.client_have_voice == False:
            conn.asr_audio = conn.asr_audio[-10:]
            return

        # If segment has voice and has stopped
        if conn.client_voice_stop:
            asr_audio_task = copy.deepcopy(conn.asr_audio)
            conn.asr_audio.clear()
            # Audio too short, cannot recognize
            conn.reset_vad_states()
            if len(asr_audio_task) > 15:
                await self.handle_voice_stop(conn, asr_audio_task)

    # Handle voice stop
    async def handle_voice_stop(self, conn, asr_audio_task):
        raw_text, _ = await self.speech_to_text(
            asr_audio_task, conn.session_id, conn.audio_format
        )  # Ensure ASR module returns raw text

        conn.logger.bind(tag=TAG).info(f"Recognized text: {raw_text}")
        text_len, _ = remove_punctuation_and_length(raw_text)
        self.stop_ws_connection()

        if text_len > 0:
            # Use custom module for reporting
            await startToChat(conn, raw_text)
            enqueue_asr_report(conn, raw_text, asr_audio_task)

    def stop_ws_connection(self):
        pass

    def save_audio_to_file(self, pcm_data: List[bytes], session_id: str) -> str:
        """Save PCM data as WAV file"""
        module_name = __name__.split(".")[-1]
        file_name = f"asr_{module_name}_{session_id}_{uuid.uuid4()}.wav"
        file_path = os.path.join(self.output_dir, file_name)

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes = 16-bit
            wf.setframerate(16000)
            wf.writeframes(b"".join(pcm_data))

        return file_path

    @abstractmethod
    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Convert speech data to text"""
        pass

    @staticmethod
    def decode_opus(opus_data: List[bytes]) -> bytes:
        """Decode Opus audio data to PCM data"""
        try:
            decoder = opuslib_next.Decoder(16000, 1)  # 16kHz, mono
            pcm_data = []
            buffer_size = 960  # Process 960 samples each time

            for opus_packet in opus_data:
                try:
                    # Use smaller buffer size for processing
                    pcm_frame = decoder.decode(opus_packet, buffer_size)
                    if pcm_frame:
                        pcm_data.append(pcm_frame)
                except opuslib_next.OpusError as e:
                    logger.bind(tag=TAG).warning(
                        f"Opus decoding error, skipping current packet: {e}")
                    continue
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Audio processing error: {e}", exc_info=True)
                    continue

            return pcm_data

        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Error occurred during audio decoding: {e}", exc_info=True)
            return []
