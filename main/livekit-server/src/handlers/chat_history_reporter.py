
import asyncio
import logging
import aiohttp
import time
import base64
from queue import Queue
import threading
from ..config.config_loader import ConfigLoader

logger = logging.getLogger("chat_history_reporter")

class ChatHistoryReporter:
    def __init__(self):
        self.report_queue = Queue()
        self.worker_thread = threading.Thread(target=self._process_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _process_queue(self):
        while True:
            try:
                chat_data = self.report_queue.get()
                if chat_data is None:
                    break
                asyncio.run(self._send_chat_history_report(chat_data))
            except Exception as e:
                logger.error(f"Error processing chat history queue: {e}")

    async def _send_chat_history_report(self, chat_data):
        """Send real-time chat data to manager-api for MySQL storage"""
        try:
            # Get manager-api configuration
            config = ConfigLoader._load_yaml_config()
            manager_api_config = config.get('manager_api', {})
            manager_api_url = manager_api_config.get('url')

            # Securely fetch server secret from database
            manager_api_secret = ConfigLoader.get_manager_api_secret()

            url = f"{manager_api_url}/agent/chat-history/report"

            # Prepare headers with authentication
            headers = {
                'Content-Type': 'application/json'
            }

            if manager_api_secret:
                headers['Authorization'] = f'Bearer {manager_api_secret}'
                logger.debug(f"🔑 Using authentication for manager-api request")
            else:
                logger.warning(f"⚠️ No manager-api secret found in database")

            if chat_data.get('audioBase64'):
                wav_data = self.opus_to_wav(chat_data['audioBase64'])
                if wav_data:
                    chat_data['audioBase64'] = base64.b64encode(wav_data).decode('utf-8')
                else:
                    chat_data['audioBase64'] = None

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=chat_data, headers=headers, timeout=5) as response:
                    response_text = await response.text()
                    logger.info(f"📡 Manager-api response status: {response.status}")
                    logger.debug(f"📡 Manager-api response body: {response_text}")

                    if response.status == 200:
                        logger.info(f"✅ Real-time chat data sent to manager-api successfully")
                    else:
                        logger.error(f"❌ Manager-api returned status {response.status}: {response_text}")
                        logger.error(f"🔍 Request URL: {url}")
                        logger.error(f"🔍 Request headers: {headers}")
                        logger.error(f"🔍 Request data: {chat_data}")

        except Exception as e:
            logger.error(f"❌ Failed to send chat data to manager-api: {e}")

    def enqueue_report(self, chat_data):
        self.report_queue.put(chat_data)

    def opus_to_wav(self, opus_data):
        """Convert Opus data to WAV format byte stream

        Args:
            opus_data: Opus audio data

        Returns:
            bytes: WAV format audio data
        """
        try:
            import opuslib_next
            decoder = opuslib_next.Decoder(16000, 1)  # 16kHz, mono
            pcm_data = []

            for opus_packet in opus_data:
                try:
                    pcm_frame = decoder.decode(opus_packet, 960)  # 960 samples = 60ms
                    pcm_data.append(pcm_frame)
                except opuslib_next.OpusError as e:
                    logger.error(f"Opus decoding error: {e}", exc_info=True)

            if not pcm_data:
                raise ValueError("No valid PCM data")

            # Create WAV file header
            pcm_data_bytes = b"".join(pcm_data)
            num_samples = len(pcm_data_bytes) // 2  # 16-bit samples

            # WAV file header
            wav_header = bytearray()
            wav_header.extend(b"RIFF")  # ChunkID
            wav_header.extend((36 + len(pcm_data_bytes)).to_bytes(4, "little"))  # ChunkSize
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
            wav_header.extend(len(pcm_data_bytes).to_bytes(4, "little"))  # Subchunk2Size

            # Return complete WAV data
            return bytes(wav_header) + pcm_data_bytes
        except Exception as e:
            logger.error(f"Failed to convert opus to wav: {e}")
            return None

chat_history_reporter = ChatHistoryReporter()
