"""
Complete Audio STT Wrapper
Integrates VAD with AWS STT for complete audio session processing
"""

import logging
from typing import Optional
from livekit.agents import stt
from .aws_stt_provider import AWSTranscribeSTT

logger = logging.getLogger("complete_audio_stt_wrapper")


class CompleteAudioSTTWrapper(stt.STT):
    """
    Wrapper that integrates VAD with AWS STT for complete audio processing.
    This ensures VAD sends complete audio sessions to AWS STT instead of individual frames.
    """
    
    def __init__(self, aws_stt: AWSTranscribeSTT, vad_instance=None):
        """Initialize the wrapper.
        
        Args:
            aws_stt: The AWS STT provider instance
            vad_instance: The VAD instance to integrate with
        """
        super().__init__(capabilities=aws_stt.capabilities)
        self._aws_stt = aws_stt
        self._vad_instance = vad_instance
        
        # Set up VAD integration
        if self._vad_instance:
            self._setup_vad_integration()
            logger.info("🔗 [STT-WRAPPER] VAD integration configured for complete audio processing")
        else:
            logger.warning("⚠️ [STT-WRAPPER] No VAD instance provided - complete audio processing disabled")
    
    def _setup_vad_integration(self):
        """Set up VAD to send complete audio to this STT provider."""
        if hasattr(self._vad_instance, 'stream'):
            # Wrap the VAD stream method to include STT provider
            original_stream_method = self._vad_instance.stream
            
            def enhanced_stream(**kwargs):
                # Always pass this STT provider to VAD streams
                kwargs['stt_provider'] = self._aws_stt
                return original_stream_method(**kwargs)
            
            self._vad_instance.stream = enhanced_stream
            logger.debug("🔗 [STT-WRAPPER] VAD stream method enhanced with STT integration")
    
    def stream(self, *, language: str = None, conn_options=None, **kwargs):
        """Create a speech stream that processes complete audio only."""
        return self._aws_stt.stream(language=language, conn_options=conn_options, **kwargs)
    
    async def _recognize_impl(self, buffer, *, language: str = None, conn_options=None, **kwargs):
        """Delegate to AWS STT implementation."""
        return await self._aws_stt._recognize_impl(
            buffer, language=language, conn_options=conn_options, **kwargs
        )
    
    async def transcribe_complete_audio(self, audio_frames: list, session_id: str = None) -> Optional[str]:
        """Transcribe complete audio session."""
        return await self._aws_stt.transcribe_complete_audio(audio_frames, session_id)
    
    @property
    def language_code(self):
        """Get the language code from AWS STT."""
        return self._aws_stt.language_code
    
    @property
    def sample_rate(self):
        """Get the sample rate from AWS STT."""
        return self._aws_stt.sample_rate
    
    def get_supported_languages(self):
        """Get supported languages from AWS STT."""
        return self._aws_stt.get_supported_languages()