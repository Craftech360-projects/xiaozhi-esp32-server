import json
import gzip
import uuid
import asyncio
import websockets
import opuslib_next
from core.providers.asr.base import ASRProviderBase
from config.logger import setup_logging
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__()
        self.interface_type = InterfaceType.STREAM
        self.config = config
        self.text = ""
        self.max_retries = 3
        self.retry_delay = 2
        self.decoder = opuslib_next.Decoder(16000, 1)
        self.asr_ws = None
        self.forward_task = None
        self.is_processing = False  # Add processing state flag

        # Configuration parameters
        self.appid = str(config.get("appid"))
        self.cluster = config.get("cluster")
        self.access_token = config.get("access_token")
        self.boosting_table_name = config.get("boosting_table_name", "")
        self.correct_table_name = config.get("correct_table_name", "")
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file

        # Volcano Engine ASR configuration
        self.ws_url = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
        self.uid = config.get("uid", "streaming_asr_service")
        self.workflow = config.get(
            "workflow", "audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate"
        )
        self.result_type = config.get("result_type", "single")
        self.format = config.get("format", "pcm")
        self.codec = config.get("codec", "pcm")
        self.rate = config.get("sample_rate", 16000)
        self.language = config.get("language", "zh-CN")
        self.bits = config.get("bits", 16)
        self.channel = config.get("channel", 1)
        self.auth_method = config.get("auth_method", "token")
        self.secret = config.get("secret", "access_secret")

    async def open_audio_channels(self, conn):
        await super().open_audio_channels(conn)

    async def receive_audio(self, conn, audio, audio_have_voice):
        conn.asr_audio.append(audio)
        conn.asr_audio = conn.asr_audio[-10:]

        # If current frame has voice and no connection established before
        if audio_have_voice and self.asr_ws is None and not self.is_processing:
            try:
                self.is_processing = True
                # Establish new WebSocket connection
                headers = self.token_auth() if self.auth_method == "token" else None
                logger.bind(tag=TAG).info(
                    f"Connecting to ASR service, headers: {headers}")

                self.asr_ws = await websockets.connect(
                    self.ws_url,
                    additional_headers=headers,
                    max_size=1000000000,
                    ping_interval=None,
                    ping_timeout=None,
                    close_timeout=10,
                )

                # Send initialization request
                request_params = self.construct_request(str(uuid.uuid4()))
                try:
                    payload_bytes = str.encode(json.dumps(request_params))
                    payload_bytes = gzip.compress(payload_bytes)

                    full_client_request = self.generate_header()
                    full_client_request.extend(
                        (len(payload_bytes)).to_bytes(4, "big"))
                    full_client_request.extend(payload_bytes)

                    logger.bind(tag=TAG).info(
                        f"Sending initialization request: {request_params}")
                    await self.asr_ws.send(full_client_request)

                    # Wait for initialization response
                    init_res = await self.asr_ws.recv()
                    result = self.parse_response(init_res)
                    logger.bind(tag=TAG).info(
                        f"Received initialization response: {result}")

                    # Check initialization response
                    if "code" in result and result["code"] != 1000:
                        error_msg = f"ASR service initialization failed: {result.get('payload_msg', {}).get('error', 'Unknown error')}"
                        logger.bind(tag=TAG).error(error_msg)
                        raise Exception(error_msg)

                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Failed to send initialization request: {str(e)}")
                    if hasattr(e, "__cause__") and e.__cause__:
                        logger.bind(tag=TAG).error(
                            f"Error cause: {str(e.__cause__)}")
                    raise e

                # Start async task to receive ASR results
                self.forward_task = asyncio.create_task(
                    self._forward_asr_results(conn))

                # Send cached audio data
                if conn.asr_audio and len(conn.asr_audio) > 0:
                    for cached_audio in conn.asr_audio[-10:]:
                        try:
                            pcm_frame = self.decoder.decode(cached_audio, 960)
                            payload = gzip.compress(pcm_frame)

                            audio_request = bytearray(
                                self.generate_audio_default_header()
                            )
                            audio_request.extend(
                                len(payload).to_bytes(4, "big"))
                            audio_request.extend(payload)

                            await self.asr_ws.send(audio_request)
                        except Exception as e:
                            logger.bind(tag=TAG).info(
                                f"Error sending cached audio data: {e}"
                            )

            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Failed to establish ASR connection: {str(e)}")
                if hasattr(e, "__cause__") and e.__cause__:
                    logger.bind(tag=TAG).error(
                        f"Error cause: {str(e.__cause__)}")
                if self.asr_ws:
                    await self.asr_ws.close()
                    self.asr_ws = None
                self.is_processing = False
                return

        # Send current audio data
        if self.asr_ws and self.is_processing:
            try:
                pcm_frame = self.decoder.decode(audio, 960)
                payload = gzip.compress(pcm_frame)

                audio_request = bytearray(self.generate_audio_default_header())
                audio_request.extend(len(payload).to_bytes(4, "big"))
                audio_request.extend(payload)

                await self.asr_ws.send(audio_request)
            except Exception as e:
                logger.bind(tag=TAG).info(f"Error sending audio data: {e}")

    async def _forward_asr_results(self, conn):
        try:
            while self.asr_ws and not conn.stop_event.is_set():
                try:
                    response = await self.asr_ws.recv()
                    result = self.parse_response(response)
                    logger.bind(tag=TAG).debug(
                        f"Received ASR result: {result}")

                    if "payload_msg" in result:
                        payload = result["payload_msg"]

                        # Check if error code is 1013 (no valid speech)
                        if "code" in payload and payload["code"] == 1013:
                            # Handle silently, don't log error
                            continue

                        if "result" in payload:
                            utterances = payload["result"].get(
                                "utterances", [])

                            # Check duration and empty text condition
                            if (
                                payload.get("audio_info", {}).get(
                                    "duration", 0) > 2000
                                and not utterances
                                and not payload["result"].get("text")
                            ):
                                logger.bind(tag=TAG).error(
                                    f"Recognized text: empty")
                                self.text = ""
                                conn.reset_vad_states()
                                await self.handle_voice_stop(conn, None)
                                break

                            for utterance in utterances:
                                if utterance.get("definite", False):
                                    self.text = utterance["text"]
                                    logger.bind(tag=TAG).info(
                                        f"Recognized text: {self.text}"
                                    )
                                    conn.reset_vad_states()
                                    await self.handle_voice_stop(conn, None)
                                    break

                        elif "error" in payload:
                            error_msg = payload.get("error", "Unknown error")
                            logger.bind(tag=TAG).error(
                                f"ASR service returned error: {error_msg}")
                            break

                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).info("ASR service connection closed")
                    self.is_processing = False
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Error processing ASR results: {str(e)}")
                    if hasattr(e, "__cause__") and e.__cause__:
                        logger.bind(tag=TAG).error(
                            f"Error cause: {str(e.__cause__)}")
                    self.is_processing = False
                    break

        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Error in ASR result forwarding task: {str(e)}")
            if hasattr(e, "__cause__") and e.__cause__:
                logger.bind(tag=TAG).error(f"Error cause: {str(e.__cause__)}")
        finally:
            if self.asr_ws:
                await self.asr_ws.close()
                self.asr_ws = None
            self.is_processing = False

    def stop_ws_connection(self):
        if self.asr_ws:
            asyncio.create_task(self.asr_ws.close())
            self.asr_ws = None
            self.is_processing = False

    def construct_request(self, reqid):
        req = {
            "app": {
                "appid": self.appid,
                "cluster": self.cluster,
                "token": self.access_token,
            },
            "user": {"uid": self.uid},
            "request": {
                "reqid": reqid,
                "workflow": self.workflow,
                "show_utterances": True,
                "result_type": self.result_type,
                "sequence": 1,
                "boosting_table_name": self.boosting_table_name,
                "correct_table_name": self.correct_table_name,
                "end_window_size": 200,
            },
            "audio": {
                "format": self.format,
                "codec": self.codec,
                "rate": self.rate,
                "language": self.language,
                "bits": self.bits,
                "channel": self.channel,
                "sample_rate": self.rate,
            },
        }

        logger.bind(tag=TAG).debug(
            f"Constructed request parameters: {json.dumps(req, ensure_ascii=False)}"
        )
        return req

    def token_auth(self):
        return {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }

    def generate_header(
        self,
        version=0x01,
        message_type=0x01,
        message_type_specific_flags=0x00,
        serial_method=0x01,
        compression_type=0x01,
        reserved_data=0x00,
        extension_header: bytes = b"",
    ):
        header = bytearray()
        header_size = int(len(extension_header) / 4) + 1
        header.append((version << 4) | header_size)
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serial_method << 4) | compression_type)
        header.append(reserved_data)
        header.extend(extension_header)
        return header

    def generate_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x00,
            serial_method=0x01,
            compression_type=0x01,
        )

    def generate_last_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x02,
            serial_method=0x01,
            compression_type=0x01,
        )

    def parse_response(self, res: bytes) -> dict:
        try:
            # Check response length
            if len(res) < 4:
                logger.bind(tag=TAG).error(
                    f"Response data length insufficient: {len(res)}")
                return {"error": "Response data length insufficient"}

            # Get message header
            header = res[:4]
            message_type = header[1] >> 4

            # If error response
            if message_type == 0x0F:  # SERVER_ERROR_RESPONSE
                code = int.from_bytes(res[4:8], "big", signed=False)
                msg_length = int.from_bytes(res[8:12], "big", signed=False)
                error_msg = json.loads(res[12:].decode("utf-8"))
                return {
                    "code": code,
                    "msg_length": msg_length,
                    "payload_msg": error_msg,
                }

            # Get JSON data (skip 12-byte header)
            try:
                json_data = res[12:].decode("utf-8")
                result = json.loads(json_data)
                logger.bind(tag=TAG).debug(
                    f"Successfully parsed JSON response: {result}")
                return {"payload_msg": result}
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.bind(tag=TAG).error(f"JSON parsing failed: {str(e)}")
                logger.bind(tag=TAG).error(f"Raw data: {res}")
                raise

        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to parse response: {str(e)}")
            logger.bind(tag=TAG).error(f"Raw response data: {res.hex()}")
            raise

    async def speech_to_text(self, opus_data, session_id, audio_format):
        result = self.text
        self.text = ""  # Clear text
        return result, None

    async def close(self):
        """Resource cleanup method"""
        if self.asr_ws:
            await self.asr_ws.close()
            self.asr_ws = None

        if self.forward_task:
            self.forward_task.cancel()
            try:
                await self.forward_task
            except asyncio.CancelledError:
                pass
            self.forward_task = None

        self.is_processing = False
