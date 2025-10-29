"""
Reusable error handling module for LiveKit agents
Provides robust error recovery for LLM, STT, and TTS components
"""

import logging
import os
import pathlib
import random
from typing import Dict, Any, Optional

from livekit.agents.utils.audio import audio_frames_from_file
from livekit.agents.voice import AgentSession
from livekit.agents.voice.events import ErrorEvent

logger = logging.getLogger("error-handler")


class ErrorRecoveryManager:
    """Manages error recovery state and fallback messages"""
    
    def __init__(self, max_retries: int = 3, custom_audio_path: Optional[str] = None):
        self.error_counts: Dict[str, int] = {}
        self.max_retries = max_retries
        self.custom_audio_path = custom_audio_path or self._get_default_audio_path()
        
        self.fallback_messages = {
            "llm": [
                "I'm having trouble processing that. Could you please try again?",
                "Let me try to help you - what did you need?", 
                "I didn't catch that properly. Could you repeat your question?",
                "Sorry, I'm having a moment. What can I help you with?"
            ],
            "stt": [
                "I'm having trouble hearing you clearly. Could you speak a bit louder?",
                "Sorry, I didn't catch that. Could you please repeat?",
                "I'm having audio issues. Please try speaking again.",
                "Could you say that again? I'm having trouble with the audio."
            ],
            "tts": [
                "I'm having trouble speaking right now, but I can still hear you.",
                "Audio output issues detected. I can still understand you though.", 
                "Having some voice problems, but I'm still listening.",
                "My voice might be having issues, but I can still help you."
            ]
        }
    
    def _get_default_audio_path(self) -> str:
        """Get default path for error audio file"""
        return os.path.join(pathlib.Path(__file__).parent.absolute(), "error_message.ogg")
    
    def get_error_type(self, source) -> str:
        """Determine error type based on source component"""
        source_name = source.__class__.__name__.lower()
        if 'llm' in source_name or 'openai' in source_name or 'anthropic' in source_name:
            return 'llm'
        elif 'stt' in source_name or 'deepgram' in source_name or 'whisper' in source_name:
            return 'stt'
        elif 'tts' in source_name or 'cartesia' in source_name or 'elevenlabs' in source_name:
            return 'tts'
        else:
            return 'unknown'
    
    def should_recover(self, error_type: str) -> bool:
        """Check if we should attempt recovery based on error count"""
        count = self.error_counts.get(error_type, 0)
        return count < self.max_retries
    
    def increment_error_count(self, error_type: str):
        """Increment error count for a specific type"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def reset_error_count(self, error_type: str):
        """Reset error count for successful recovery"""
        if error_type in self.error_counts:
            self.error_counts[error_type] = 0
    
    def get_fallback_message(self, error_type: str) -> str:
        """Get a random fallback message for the error type"""
        messages = self.fallback_messages.get(error_type, self.fallback_messages['llm'])
        return random.choice(messages)
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get current error statistics"""
        return self.error_counts.copy()


def setup_error_handling(session: AgentSession, max_retries: int = 3, custom_audio_path: Optional[str] = None) -> ErrorRecoveryManager:
    """
    Set up comprehensive error handling for a LiveKit AgentSession
    
    Args:
        session: The AgentSession to add error handling to
        max_retries: Maximum retry attempts per error type
        custom_audio_path: Path to custom error audio file
        
    Returns:
        ErrorRecoveryManager instance for monitoring
    """
    error_manager = ErrorRecoveryManager(max_retries, custom_audio_path)
    
    @session.on("error")
    def on_error(ev: ErrorEvent):
        """Enhanced error handler with proper recovery mechanisms"""
        error_type = error_manager.get_error_type(ev.source)
        error_message = str(ev.error)
        
        logger.error(f"🚨 {error_type.upper()} Error: {error_message}")
        logger.error(f"🔍 Error source: {ev.source.__class__.__name__}")
        logger.error(f"🔄 Recoverable: {ev.error.recoverable}")
        
        # Check if this is already marked as recoverable by LiveKit
        if ev.error.recoverable:
            logger.info(f"✅ Error marked as recoverable, letting LiveKit handle it")
            return
        
        # Determine if we should attempt recovery
        should_recover = error_manager.should_recover(error_type)
        error_manager.increment_error_count(error_type)
        
        logger.info(f"🔄 Error count for {error_type}: {error_manager.error_counts.get(error_type, 0)}/{error_manager.max_retries}")
        
        if should_recover:
            # Attempt recovery based on error type
            if error_type == 'llm':
                _handle_llm_error(session, error_manager, ev)
                return
            elif error_type == 'tts':
                _handle_tts_error(session, error_manager, ev)
                return
            elif error_type == 'stt':
                _handle_stt_error(session, error_manager, ev)
                return
        
        # Unrecoverable error or max retries reached
        _handle_unrecoverable_error(session, error_manager, error_type, error_message)
    
    # Success handlers to reset error counts
    @session.on("agent_speech_committed")
    def on_speech_committed(text: str):
        """Reset TTS error count on successful speech"""
        error_manager.reset_error_count('tts')
        logger.debug("✅ TTS working - error count reset")
    
    @session.on("user_speech_committed") 
    def on_user_speech_committed(text: str):
        """Reset STT error count on successful speech recognition"""
        error_manager.reset_error_count('stt')
        logger.debug("✅ STT working - error count reset")
    
    @session.on("function_calls_finished")
    def on_function_calls_finished():
        """Reset LLM error count on successful function execution"""
        error_manager.reset_error_count('llm')
        logger.debug("✅ LLM working - error count reset")
    
    logger.info("🛡️ Error handling setup complete")
    return error_manager


def _handle_llm_error(session: AgentSession, error_manager: ErrorRecoveryManager, ev: ErrorEvent):
    """Handle LLM-specific errors"""
    logger.info("🔄 Attempting LLM error recovery...")
    ev.error.recoverable = True
    
    # Provide fallback message using session.say
    fallback_msg = error_manager.get_fallback_message('llm')
    try:
        session.say(fallback_msg, allow_interruptions=True)
        logger.info("✅ LLM fallback message delivered")
    except Exception as say_error:
        logger.warning(f"⚠️ Could not deliver fallback message via TTS: {say_error}")
        # Try with custom audio if available
        if os.path.exists(error_manager.custom_audio_path):
            try:
                session.say(
                    fallback_msg,
                    audio=audio_frames_from_file(error_manager.custom_audio_path),
                    allow_interruptions=False
                )
                logger.info("✅ LLM fallback delivered via custom audio")
            except Exception as audio_error:
                logger.error(f"❌ Failed to deliver audio fallback: {audio_error}")


def _handle_tts_error(session: AgentSession, error_manager: ErrorRecoveryManager, ev: ErrorEvent):
    """Handle TTS-specific errors"""
    logger.info("🔄 Attempting TTS error recovery...")
    ev.error.recoverable = True
    
    # For TTS errors, try to use custom audio file if available
    fallback_msg = error_manager.get_fallback_message('tts')
    if os.path.exists(error_manager.custom_audio_path):
        try:
            session.say(
                fallback_msg,
                audio=audio_frames_from_file(error_manager.custom_audio_path),
                allow_interruptions=False
            )
            logger.info("✅ Used custom audio for TTS fallback")
        except Exception as audio_error:
            logger.error(f"❌ Custom audio fallback failed: {audio_error}")
    else:
        logger.warning("⚠️ No custom audio file available for TTS fallback")


def _handle_stt_error(session: AgentSession, error_manager: ErrorRecoveryManager, ev: ErrorEvent):
    """Handle STT-specific errors"""
    logger.info("🔄 Attempting STT error recovery...")
    
    try:
        # Reset the agent to reinitialize STT stream
        session.update_agent(session.current_agent)
        ev.error.recoverable = True
        
        # Provide feedback about audio issues
        fallback_msg = error_manager.get_fallback_message('stt')
        session.say(fallback_msg, allow_interruptions=True)
        
        logger.info("✅ STT recovery attempted - agent updated")
        
    except Exception as recovery_error:
        logger.error(f"❌ STT recovery failed: {recovery_error}")
        # Don't mark as recoverable if recovery failed


def _handle_unrecoverable_error(session: AgentSession, error_manager: ErrorRecoveryManager, error_type: str, error_message: str):
    """Handle unrecoverable errors"""
    logger.error(f"❌ Unrecoverable {error_type} error or max retries reached")
    
    # Provide final fallback message
    final_message = "I'm experiencing technical difficulties. Please try reconnecting or contact support if the problem persists."
    
    try:
        if os.path.exists(error_manager.custom_audio_path):
            session.say(
                final_message,
                audio=audio_frames_from_file(error_manager.custom_audio_path),
                allow_interruptions=False,
            )
        else:
            session.say(final_message, allow_interruptions=False)
    except Exception as final_error:
        logger.error(f"❌ Failed to deliver final error message: {final_error}")
    
    # Log final error state
    logger.error(f"🔚 Session ending due to unrecoverable {error_type} error: {error_message}")