import os
import uuid
import edge_tts
from datetime import datetime
from core.providers.tts.base import TTSProviderBase
from config.logger import setup_logging
from core.providers.llm.langfuse_wrapper import langfuse_tracker

TAG = __name__
logger = setup_logging()

class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice")
        self.audio_file_type = config.get("format", "mp3")

    def generate_filename(self, extension=".mp3"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}",
        )

    @langfuse_tracker.track_tts("edge_tts")
    async def text_to_speak(self, text, output_file):
        logger.bind(tag=TAG).info(f"Generating TTS for text: '{text}' with voice: {self.voice}")
        try:
            communicate = edge_tts.Communicate(text, voice=self.voice)
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                logger.bind(tag=TAG).info(f"Successfully generated TTS audio to file: {output_file}")
            else:
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                logger.bind(tag=TAG).info(f"Successfully generated TTS audio bytes, length: {len(audio_bytes)}")
                return audio_bytes
        except Exception as e:
            error_msg = f"Edge TTS request failed: {e}"
            logger.bind(tag=TAG).error(error_msg)
            raise Exception(error_msg) from e