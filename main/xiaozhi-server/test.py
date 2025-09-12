import os
import queue
import threading
import time
from typing import Generator, Iterator

import pyaudio
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions
from google.oauth2 import service_account

PROJECT_ID = 'gen-lang-client-0652043794'
CREDENTIALS_FILE = 'gen-lang-client-0652043794-e5f4175261a8.json'

# Audio recording parameters
RATE = 16000  # Sample rate
CHUNK = int(RATE / 10)  # 100ms chunks
CHANNELS = 1
FORMAT = pyaudio.paInt16

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    
    def __init__(self, rate: int = RATE, chunk: int = CHUNK, channels: int = CHANNELS):
        self._rate = rate
        self._chunk = chunk
        self._channels = channels
        self._buff = queue.Queue()
        self.closed = True
        self._audio_interface = None
        self._audio_stream = None

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=FORMAT,
            channels=self._channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        """Close the audio stream and PyAudio interface."""
        self.closed = True
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self) -> Generator[bytes, None, None]:
        """Generator that yields audio chunks from the microphone."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def transcribe_streaming_mic(duration_seconds: int = 60) -> None:
    """Transcribes audio from microphone using Google Cloud Speech-to-Text V2 API.

    Args:
        duration_seconds (int): How long to listen to the microphone (default: 60 seconds)
    """
    print(f"Starting microphone transcription for {duration_seconds} seconds...")
    print("Speak into your microphone...")

    # Load credentials from service account file
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
    
    # Instantiate the client
    client = SpeechClient(
        credentials=credentials,
        client_options=ClientOptions(
            api_endpoint="us-central1-speech.googleapis.com",
        )
    )

    # Configure recognition
    recognition_config = cloud_speech.RecognitionConfig(
        explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
            sample_rate_hertz=RATE,
            encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
            audio_channel_count=CHANNELS,
        ),
        language_codes=["en-US"],
        model="chirp_2",
        features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        ),
    )

    streaming_config = cloud_speech.StreamingRecognitionConfig(
        config=recognition_config,
        streaming_features=cloud_speech.StreamingRecognitionFeatures(
            interim_results=True,
        ),
    )

    def request_generator(
        mic_stream: MicrophoneStream,
    ) -> Iterator[cloud_speech.StreamingRecognizeRequest]:
        """Generator that yields streaming recognition requests."""
        # First, send the configuration request
        config_request = cloud_speech.StreamingRecognizeRequest(
            recognizer=f"projects/{PROJECT_ID}/locations/us-central1/recognizers/_",
            streaming_config=streaming_config,
        )
        yield config_request

        # Then yield audio requests
        for chunk in mic_stream.generator():
            yield cloud_speech.StreamingRecognizeRequest(audio=chunk)

    # Start recording and transcribing
    with MicrophoneStream() as stream:
        try:
            # Set up the streaming recognition
            responses = client.streaming_recognize(
                requests=request_generator(stream)
            )
            
            start_time = time.time()
            
            # Process the responses
            for response in responses:
                # Check if we've exceeded the duration
                if time.time() - start_time > duration_seconds:
                    break
                    
                if not response.results:
                    continue

                # Get the most recent result
                result = response.results[0]
                
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript

                # Check if this is a final result or interim
                if result.is_final:
                    print(f"Final: {transcript}")
                    print("-" * 50)
                else:
                    # Interim results - show in real-time
                    print(f"Interim: {transcript}", end="\r")
                    
        except KeyboardInterrupt:
            print("\nStopping transcription...")
        except Exception as e:
            print(f"Error during transcription: {e}")

    print("\nTranscription finished.")


def transcribe_streaming_mic_simple(duration_seconds: int = 30) -> None:
    """Simplified version with basic error handling."""
    print(f"Listening for {duration_seconds} seconds. Press Ctrl+C to stop early.")
    
    try:
        transcribe_streaming_mic(duration_seconds)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have:")
        print("1. Set up Google Cloud authentication")
        print("2. Installed required packages: pip install google-cloud-speech pyaudio")
        print("3. A working microphone")


if __name__ == "__main__":
    # Example usage
    transcribe_streaming_mic_simple(60)  # Listen for 60 seconds