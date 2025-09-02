import json
import time
from core.handle.abortHandle import handleAbortMessage
from core.handle.helloHandle import handleHelloMessage
from core.providers.tools.device_mcp import handle_mcp_message
from core.utils.util import remove_punctuation_and_length, filter_sensitive_info
from core.handle.receiveAudioHandle import startToChat, handleAudioMessage
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.providers.tools.device_iot import handleIotDescriptors, handleIotStatus
from core.handle.reportHandle import enqueue_asr_report
import asyncio

TAG = __name__


def is_educational_query(text):
    """
    Basic educational query detection for text handler
    This provides an early filter before reaching the memory provider
    """
    if not text or not isinstance(text, str):
        return False
    
    text_lower = text.lower().strip()
    
    # Educational keywords that indicate learning content
    educational_keywords = [
        # Mathematics
        'math', 'number', 'add', 'subtract', 'multiply', 'divide', 'fraction', 'decimal',
        'prime', 'area', 'perimeter', 'angle', 'geometry', 'algebra', 'equation', 'solve',
        'calculate', 'pattern', 'ratio', 'proportion', 'percentage', 'symmetry', 'integer',
        # Science  
        'science', 'physics', 'chemistry', 'biology', 'experiment', 'element', 'compound',
        'cell', 'organism', 'energy', 'force', 'motion', 'light', 'sound', 'heat',
        # English
        'grammar', 'noun', 'verb', 'adjective', 'sentence', 'paragraph', 'essay', 'story',
        'poem', 'literature', 'reading', 'writing', 'vocabulary', 'spelling',
        # Educational questions
        'what is', 'what are', 'how to', 'explain', 'describe', 'define', 'tell me about',
        'help me understand', 'teach me', 'learn', 'study', 'homework', 'assignment',
        # NCERT specific
        'chapter', 'lesson', 'exercise', 'question', 'textbook', 'ncert', 'standard', 'class'
    ]
    
    # Check if any educational keywords are present
    for keyword in educational_keywords:
        if keyword in text_lower:
            return True
    
    return False


def enhance_educational_query(text):
    """
    Enhance educational queries with context for better processing
    """
    if not is_educational_query(text):
        return text
    
    # Add minimal context enhancement while preserving original query
    text_lower = text.lower()
    
    # If it's a mathematical query, add slight context
    if any(math_word in text_lower for math_word in ['math', 'number', 'add', 'subtract', 'multiply', 'divide', 'fraction', 'area', 'perimeter']):
        # Don't modify the original text, just mark it for potential processing
        return text
    
    return text


async def handleTextMessage(conn, message):
    """Handle text messages"""
    try:
        msg_json = json.loads(message)
        if isinstance(msg_json, int):
            conn.logger.bind(tag=TAG).info(f"Received text message: {message}")
            await conn.websocket.send(message)
            return
        if msg_json["type"] == "hello":
            conn.logger.bind(tag=TAG).info(
                f"Received hello message: {message}")
            await handleHelloMessage(conn, msg_json)
        elif msg_json["type"] == "abort":
            conn.logger.bind(tag=TAG).info(
                f"Received abort message: {message}")
            await handleAbortMessage(conn)
        elif msg_json["type"] == "listen":
            conn.logger.bind(tag=TAG).info(
                f"Received listen message: {message}")
            if "mode" in msg_json:
                conn.client_listen_mode = msg_json["mode"]
                conn.logger.bind(tag=TAG).debug(
                    f"Client audio capture mode: {conn.client_listen_mode}"
                )
            if msg_json["state"] == "start":
                # Reset VAD states to clear any leftover audio from previous session
                conn.reset_vad_states()
                # Mark that we just started listening to prevent processing stale audio
                conn.just_started_listening = True
                # Set a timestamp for when we started listening
                conn.listen_start_time = time.time()
                # Add initial connection flag to prevent false positive on first audio
                if not hasattr(conn, "initial_connection_handled"):
                    conn.initial_connection_handled = False
                    conn.initial_connection_time = asyncio.get_event_loop().time()
                conn.client_have_voice = True
                conn.client_voice_stop = False
            elif msg_json["state"] == "stop":
                conn.client_have_voice = True
                conn.client_voice_stop = True
                if len(conn.asr_audio) > 0:
                    await handleAudioMessage(conn, b"")
            elif msg_json["state"] == "detect":
                conn.client_have_voice = False
                conn.asr_audio.clear()
                if "text" in msg_json:
                    conn.last_activity_time = time.time() * 1000
                    original_text = msg_json["text"]  # Preserve original text
                    filtered_len, filtered_text = remove_punctuation_and_length(
                        original_text
                    )

                    # Identify if it's a wake-up word
                    is_wakeup_words = filtered_text in conn.config.get(
                        "wakeup_words")
                    # Whether wake-up word reply is enabled
                    enable_greeting = conn.config.get("enable_greeting", True)

                    if is_wakeup_words and not enable_greeting:
                        # If it's a wake-up word and wake-up word reply is disabled, no need to respond
                        await send_stt_message(conn, original_text)
                        await send_tts_message(conn, "stop", None)
                        conn.client_is_speaking = False
                    elif is_wakeup_words:
                        conn.just_woken_up = True
                        # Report plain text data (reuse ASR reporting function, but provide no audio data)
                        enqueue_asr_report(conn, "Hey, hello there", [])
                        await startToChat(conn, "Hey, hello there")
                    else:
                        # Check if it's an educational query for enhanced processing
                        processed_text = original_text
                        if is_educational_query(original_text):
                            conn.logger.bind(tag=TAG).info(f"Educational query detected: {original_text}")
                            processed_text = enhance_educational_query(original_text)
                        
                        # Report plain text data (reuse ASR reporting function, but provide no audio data)
                        enqueue_asr_report(conn, original_text, [])
                        # Otherwise, need LLM to respond to text content
                        await startToChat(conn, processed_text)
        elif msg_json["type"] == "iot":
            conn.logger.bind(tag=TAG).info(f"Received iot message: {message}")
            if "descriptors" in msg_json:
                asyncio.create_task(handleIotDescriptors(
                    conn, msg_json["descriptors"]))
            if "states" in msg_json:
                asyncio.create_task(handleIotStatus(conn, msg_json["states"]))
        elif msg_json["type"] == "mcp":
            conn.logger.bind(tag=TAG).info(
                f"Received mcp message: {message[:100]}")
            if "payload" in msg_json:
                asyncio.create_task(
                    handle_mcp_message(conn, conn.mcp_client,
                                       msg_json["payload"])
                )
        elif msg_json["type"] == "server":
            # Filter sensitive information when logging
            conn.logger.bind(tag=TAG).info(
                f"Received server message: {filter_sensitive_info(msg_json)}"
            )
            # If configuration is read from API, need to verify secret
            if not conn.read_config_from_api:
                return
            # Get secret from post request
            post_secret = msg_json.get("content", {}).get("secret", "")
            secret = conn.config["manager-api"].get("secret", "")
            # If secret doesn't match, return
            if post_secret != secret:
                await conn.websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": "Server secret verification failed",
                        }
                    )
                )
                return
            # Dynamically update configuration
            if msg_json["action"] == "update_config":
                try:
                    # Update WebSocketServer configuration
                    if not conn.server:
                        await conn.websocket.send(
                            json.dumps(
                                {
                                    "type": "server",
                                    "status": "error",
                                    "message": "Cannot get server instance",
                                    "content": {"action": "update_config"},
                                }
                            )
                        )
                        return

                    if not await conn.server.update_config():
                        await conn.websocket.send(
                            json.dumps(
                                {
                                    "type": "server",
                                    "status": "error",
                                    "message": "Failed to update server configuration",
                                    "content": {"action": "update_config"},
                                }
                            )
                        )
                        return

                    # Send success response
                    await conn.websocket.send(
                        json.dumps(
                            {
                                "type": "server",
                                "status": "success",
                                "message": "Configuration updated successfully",
                                "content": {"action": "update_config"},
                            }
                        )
                    )
                except Exception as e:
                    conn.logger.bind(tag=TAG).error(
                        f"Failed to update configuration: {str(e)}")
                    await conn.websocket.send(
                        json.dumps(
                            {
                                "type": "server",
                                "status": "error",
                                "message": f"Failed to update configuration: {str(e)}",
                                "content": {"action": "update_config"},
                            }
                        )
                    )
            # Restart server
            elif msg_json["action"] == "restart":
                await conn.handle_restart(msg_json)
        else:
            conn.logger.bind(tag=TAG).error(
                f"Received unknown type message: {message}")
    except json.JSONDecodeError:
        await conn.websocket.send(message)
