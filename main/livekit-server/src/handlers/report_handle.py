"""
Chat history reporting functionality.

Reporting functionality includes:
1. Each agent session has its own reporting queue and processing thread.
2. The reporting thread's lifecycle is bound to the agent session.
3. Use enqueue_agent_report and enqueue_user_report for reporting.
"""

import time
import logging
from queue import Queue
import threading

from src.config.manage_api_client import report as manage_report
from src.config.config_loader import ConfigLoader

TAG = __name__
logger = logging.getLogger(TAG)

def report(session, chat_type, text, report_time):
    """Execute chat history reporting operation"""
    try:
        # In livekit-server, the mac_address might be part of the participant identity
        # and session_id is the room name.
        # This needs to be handled where the report is called.
        mac_address = getattr(session, 'mac_address', 'unknown')
        session_id = getattr(session, 'session_id', 'unknown')

        logger.info(f"📝 CHAT_HISTORY_API_ATTEMPT: [{chat_type}] {mac_address} | {session_id} | {text[:50]}...")

        # Try to send to manager-api endpoint (this may fail if endpoint doesn't exist)
        try:
            result = manage_report(
                mac_address=mac_address,
                session_id=session_id,
                chat_type=chat_type,
                content=text,
                report_time=report_time,
            )
            logger.info(f"✅ Chat history API call successful: {result}")
        except Exception as api_error:
            logger.warning(f"⚠️ Manager-api endpoint not available (using direct DB instead): {api_error}")
            # This is fine - direct database saving is already working

    except Exception as e:
        logger.error(f"❌ Chat history reporting failed: {e}")

def enqueue_agent_report(session, text):
    chat_history_config = ConfigLoader.get_chat_history_config()
    if not chat_history_config.get('enabled'):
        logger.debug("Chat history NOT SAVED - Disabled in configuration")
        return
    if chat_history_config.get('mode') == 0:
        logger.debug("Chat history NOT SAVED - Disabled in configuration (mode = 0)")
        return

    try:
        if hasattr(session, 'report_queue'):
            session.report_queue.put((2, text, int(time.time())))
            logger.info(
                f"Agent chat history queued for DATABASE (device: {getattr(session, 'mac_address', 'unknown')})"
            )
        else:
            logger.warning("Session does not have report_queue - chat history not saved")
    except Exception as e:
        logger.error(f"Failed to add agent chat to reporting queue: {text}, {e}")

def enqueue_user_report(session, text):
    chat_history_config = ConfigLoader.get_chat_history_config()
    if not chat_history_config.get('enabled'):
        logger.debug("Chat history NOT SAVED - Disabled in configuration")
        return
    if chat_history_config.get('mode') == 0:
        logger.debug("Chat history NOT SAVED - Disabled in configuration (mode = 0)")
        return

    try:
        if hasattr(session, 'report_queue'):
            session.report_queue.put((1, text, int(time.time())))
            logger.info(
                f"User chat history queued for DATABASE (device: {getattr(session, 'mac_address', 'unknown')})"
            )
        else:
            logger.warning("Session does not have report_queue - chat history not saved")
    except Exception as e:
        logger.debug(f"Failed to add user chat to reporting queue: {text}, {e}")

def run_report_thread(session):
    """Reporting thread main function"""
    while getattr(session, 'is_active', True):
        try:
            chat_type, text, report_time = session.report_queue.get(timeout=1)
            report(session, chat_type, text, report_time)
            session.report_queue.task_done()
        except Exception as e:
            # Queue empty or other exceptions
            pass
    logger.info("Report thread stopped.")

def start_report_thread(session):
    """Start the reporting thread for a session"""
    session.report_queue = Queue()
    session.is_active = True
    thread = threading.Thread(target=run_report_thread, args=(session,))
    thread.daemon = True
    thread.start()
    session.report_thread = thread
    logger.info("Report thread started.")

def stop_report_thread(session):
    """Stop the reporting thread for a session"""
    if hasattr(session, 'report_thread') and session.report_thread.is_alive():
        session.is_active = False
        session.report_thread.join()
        logger.info("Report thread joined.")
