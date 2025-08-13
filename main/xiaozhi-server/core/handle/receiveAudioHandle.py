from core.handle.sendAudioHandle import send_stt_message
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.abortHandle import handleAbortMessage
import time
import asyncio
from core.handle.sendAudioHandle import SentenceType
from core.utils.util import audio_to_data

TAG = __name__


async def handleAudioMessage(conn, audio):
    # Whether there is someone speaking in the current segment
    have_voice = conn.vad.is_vad(conn, audio)
    # If the device has just been woken up, briefly ignore VAD detection
    if have_voice and hasattr(conn, "just_woken_up") and conn.just_woken_up:
        have_voice = False
        # Set a brief delay before resuming VAD detection
        conn.asr_audio.clear()
        if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
            conn.vad_resume_task = asyncio.create_task(
                resume_vad_detection(conn))
        return

    if have_voice:
        if conn.client_is_speaking:
            await handleAbortMessage(conn)
    # Device long-term idle detection, used for say goodbye
    await no_voice_close_connect(conn, have_voice)
    # Receive audio
    await conn.asr.receive_audio(conn, audio, have_voice)


async def resume_vad_detection(conn):
    # Wait 2 seconds before resuming VAD detection
    await asyncio.sleep(1)
    conn.just_woken_up = False


async def startToChat(conn, text):
    if conn.need_bind:
        await check_bind_device(conn)
        return

    # If the daily output word count exceeds the limit
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return
    if conn.client_is_speaking:
        await handleAbortMessage(conn)

    # First perform intent analysis
    intent_handled = await handle_user_intent(conn, text)

    if intent_handled:
        # If intent has been handled, no longer proceed with chat
        return

    # Intent not handled, continue with regular chat process
    await send_stt_message(conn, text)
    conn.executor.submit(conn.chat, text)


async def no_voice_close_connect(conn, have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # Only perform timeout check when timestamp has been initialized
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info(
                    "Ending conversation, no need to send ending prompt")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "Please start with ```Time flies so fast``` and use emotional, reluctant words to end this conversation!"
            await startToChat(conn, prompt)


async def max_out_size(conn):
    text = "Sorry, I'm a bit busy right now. Let's chat again at this time tomorrow, it's a deal! See you tomorrow, bye!"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets, _ = audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn):
    if conn.bind_code:
        # Ensure bind_code is a 6-digit number
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(
                f"Invalid binding code format: {conn.bind_code}")
            text = "Binding code format error, please check the configuration."
            await send_stt_message(conn, text)
            return

        text = f"Please log into the control panel and enter {conn.bind_code} to bind the device."
        await send_stt_message(conn, text)

        # Play notification sound
        music_path = "config/assets/bind_code.wav"
        opus_packets, _ = audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # Play digits one by one
        for i in range(6):  # Ensure only 6 digits are played
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets, _ = audio_to_data(num_path)
                conn.tts.tts_audio_queue.put(
                    (SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(
                    f"Failed to play digit audio: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        text = f"Version information for this device was not found. Please configure the OTA address correctly and recompile the firmware."
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets, _ = audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
