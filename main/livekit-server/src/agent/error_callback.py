import asyncio
import logging
import os
import pathlib
import random
from typing import Dict, Any

from dotenv import load_dotenv

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.utils.audio import audio_frames_from_file
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.events import CloseEvent, ErrorEvent
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.rtc import ParticipantKind

logger = logging.getLogger("error-callback-agent")
logger.setLevel(logging.INFO)

load_dotenv()


# Enhanced error handling for STT, TTS, and LLM with proper recovery mechanisms
# This implementation follows LiveKit best practices for error recovery

class ErrorRecoveryManager:
    """Manages error recovery state and fallback messages"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.max_retries = 3
        self.fallback_messages = {
            "llm": [
                "I'm having trouble processing that. Could you please try again?",
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
    
    def get_error_type(self, source) -> str:
        """Determine error type based on source component"""
        source_name = source.__class__.__name__.lower()
        if 'llm' in source_name or 'openai' in source_name:
            return 'llm'
        elif 'stt' in source_name or 'deepgram' in source_name:
            return 'stt'
        elif 'tts' in source_name or 'cartesia' in source_name:
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
        self.error_counts[error_type] = 0
    
    def get_fallback_message(self, error_type: str) -> str:
        """Get a random fallback message for the error type"""
        messages = self.fallback_messages.get(error_type, self.fallback_messages['llm'])
        return random.choice(messages)


async def entrypoint(ctx: JobContext):
    # Initialize error recovery manager
    error_manager = ErrorRecoveryManager()
    
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
    )

    custom_error_audio = os.path.join(pathlib.Path(__file__).parent.absolute(), "error_message.ogg")

    @session.on("error")
    def on_error(ev: ErrorEvent):
        """Enhanced error handler with proper recovery mechanisms"""
        error_type = error_manager.get_error_type(ev.source)
        error_message = str(ev.error)
        
        logger.error(f"🚨 {error_type.upper()} Error: {error_message}")
        logger.error(f"🔍 Error source: {ev.source.__class__.__name__}")
        logger.error(f"🔄 Recoverable: {ev.error.recoverable}")
        
        # Check if this is a recoverable error that we should handle
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
                # LLM errors - mark as recoverable since LLM is recreated for each response
                logger.info("🔄 Attempting LLM error recovery...")
                ev.error.recoverable = True
                
                # Provide fallback message using session.say to bypass TTS if needed
                fallback_msg = error_manager.get_fallback_message('llm')
                try:
                    session.say(fallback_msg, allow_interruptions=True)
                except Exception as say_error:
                    logger.warning(f"⚠️ Could not deliver fallback message via TTS: {say_error}")
                    # Try with custom audio if available
                    if os.path.exists(custom_error_audio):
                        try:
                            session.say(
                                fallback_msg,
                                audio=audio_frames_from_file(custom_error_audio),
                                allow_interruptions=False
                            )
                        except Exception as audio_error:
                            logger.error(f"❌ Failed to deliver audio fallback: {audio_error}")
                
                return
            
            elif error_type == 'tts':
                # TTS errors - mark as recoverable since TTS is recreated for each response
                logger.info("🔄 Attempting TTS error recovery...")
                ev.error.recoverable = True
                
                # For TTS errors, try to use custom audio file if available
                fallback_msg = error_manager.get_fallback_message('tts')
                if os.path.exists(custom_error_audio):
                    try:
                        session.say(
                            fallback_msg,
                            audio=audio_frames_from_file(custom_error_audio),
                            allow_interruptions=False
                        )
                        logger.info("✅ Used custom audio for TTS fallback")
                    except Exception as audio_error:
                        logger.error(f"❌ Custom audio fallback failed: {audio_error}")
                else:
                    logger.warning("⚠️ No custom audio file available for TTS fallback")
                
                return
            
            elif error_type == 'stt':
                # STT errors - more complex recovery since STT stream persists
                logger.info("🔄 Attempting STT error recovery...")
                
                try:
                    # Reset the agent to reinitialize STT stream
                    session.update_agent(session.current_agent)
                    ev.error.recoverable = True
                    
                    # Provide feedback about audio issues
                    fallback_msg = error_manager.get_fallback_message('stt')
                    session.say(fallback_msg, allow_interruptions=True)
                    
                    logger.info("✅ STT recovery attempted - agent updated")
                    return
                    
                except Exception as recovery_error:
                    logger.error(f"❌ STT recovery failed: {recovery_error}")
                    # Fall through to unrecoverable handling
        
        # Unrecoverable error or max retries reached
        logger.error(f"❌ Unrecoverable {error_type} error or max retries reached")
        
        # Provide final fallback message
        final_message = "I'm experiencing technical difficulties. Please try reconnecting or contact support if the problem persists."
        
        try:
            if os.path.exists(custom_error_audio):
                session.say(
                    final_message,
                    audio=audio_frames_from_file(custom_error_audio),
                    allow_interruptions=False,
                )
            else:
                session.say(final_message, allow_interruptions=False)
        except Exception as final_error:
            logger.error(f"❌ Failed to deliver final error message: {final_error}")
        
        # Log final error state
        logger.error(f"🔚 Session ending due to unrecoverable {error_type} error: {error_message}")
        
        # Don't mark as recoverable - let the session close

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

    @session.on("close")
    def on_close(_: CloseEvent):
        logger.info("🔚 Session is closing")
        
        # Log final error statistics
        if error_manager.error_counts:
            logger.info(f"📊 Final error counts: {error_manager.error_counts}")
        else:
            logger.info("📊 No errors encountered during session")

        # SIP transfer logic (if applicable)
        try:
            participants = [
                p for p in ctx.room.remote_participants.values()
                if p.kind == ParticipantKind.PARTICIPANT_KIND_SIP
            ]
            
            if participants:
                participant = participants[0]
                
                def on_sip_transfer_done(f: asyncio.Future):
                    if f.exception():
                        logger.error(f"❌ Error transferring SIP participant: {f.exception()}")
                    else:
                        logger.info("✅ SIP participant transferred")
                    ctx.delete_room()

                # See https://docs.livekit.io/sip/ on how to set up SIP participants
                ctx.transfer_sip_participant(participant, "tel:+18003310500").add_done_callback(
                    on_sip_transfer_done
                )
            else:
                logger.info("ℹ️ No SIP participants to transfer")
                
        except Exception as e:
            logger.warning(f"⚠️ Error in SIP transfer logic: {e}")
            # Still delete room even if SIP transfer fails
            try:
                ctx.delete_room()
            except Exception as delete_error:
                logger.error(f"❌ Failed to delete room: {delete_error}")

    # Create agent with enhanced instructions
    agent_instructions = """You are a helpful AI assistant. 

If you encounter any technical issues:
- Stay calm and try to continue the conversation
- Let the user know if you're having trouble with specific functions
- Always try to be helpful even if some features aren't working

You have access to various tools and services, but if any fail, gracefully handle the situation and offer alternatives when possible."""

    agent = Agent(instructions=agent_instructions)
    
    logger.info("🚀 Starting enhanced error-handling agent session...")
    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
