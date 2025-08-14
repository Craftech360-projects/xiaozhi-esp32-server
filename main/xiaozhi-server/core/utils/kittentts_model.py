"""
KittenTTS model implementation - copied and adapted from KittenTTS project
Ultra-lightweight text-to-speech model with ONNX runtime
"""

import json
import os
import re
import numpy as np
import phonemizer
import soundfile as sf
import onnxruntime as ort
import subprocess
import platform
from huggingface_hub import hf_hub_download


def basic_english_tokenize(text):
    """Basic English tokenizer that splits on whitespace and punctuation."""
    tokens = re.findall(r"\w+|[^\w\s]", text)
    return tokens


class WindowsEspeakPhonemizerWrapper:
    """Custom eSpeak wrapper for Windows that bypasses phonemizer detection issues"""
    
    def __init__(self, espeak_executable):
        self.espeak_executable = espeak_executable
        
    def phonemize(self, texts):
        """Phonemize texts using direct eSpeak subprocess calls"""
        results = []
        for text in texts:
            try:
                # Use eSpeak to get phonemes with IPA output
                cmd = [
                    self.espeak_executable,
                    "-q",  # quiet (no audio output)
                    "--ipa",  # IPA phonetic output
                    text
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      timeout=10, encoding='utf-8', errors='ignore')
                if result.returncode == 0 and result.stdout:
                    phonemes = result.stdout.strip()
                    results.append(phonemes)
                else:
                    # Fallback: return original text if eSpeak fails
                    results.append(text)
                    
            except Exception as e:
                print(f"eSpeak phonemization failed for '{text}': {e}")
                # Fallback: return original text
                results.append(text)
                
        return results


class TextCleaner:
    def __init__(self, dummy=None):
        _pad = "$"
        _punctuation = ';:,.!?¡¿—…"«»"" '
        _letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        _letters_ipa = "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"

        symbols = [_pad] + list(_punctuation) + list(_letters) + list(_letters_ipa)
        
        dicts = {}
        for i in range(len(symbols)):
            dicts[symbols[i]] = i

        self.word_index_dictionary = dicts

    def __call__(self, text):
        indexes = []
        for char in text:
            try:
                indexes.append(self.word_index_dictionary[char])
            except KeyError:
                pass
        return indexes


class KittenTTSModel:
    def __init__(self, model_path="kitten_tts_nano_preview.onnx", voices_path="voices.npz"):
        """Initialize KittenTTS with model and voice data.
        
        Args:
            model_path: Path to the ONNX model file
            voices_path: Path to the voices NPZ file
        """
        self.model_path = model_path
        self.voices = np.load(voices_path)
        self.session = ort.InferenceSession(model_path)
        
        # Try to initialize phonemizer with fallback options
        import platform
        import subprocess
        
        # For Windows, we need to handle eSpeak-NG path issues
        if platform.system() == "Windows":
            # Set environment variables that phonemizer might use
            espeak_dir = r"C:\Program Files\eSpeak NG"
            espeak_exe = os.path.join(espeak_dir, "espeak.exe")
            
            if os.path.exists(espeak_exe):
                # Set various environment variables that phonemizer might check
                os.environ["PHONEMIZER_ESPEAK_EXECUTABLE"] = espeak_exe
                os.environ["ESPEAK_EXECUTABLE"] = espeak_exe
                os.environ["ESPEAK_DATA_PATH"] = os.path.join(espeak_dir, "espeak-ng-data")
                
                # Add to PATH
                current_path = os.environ.get("PATH", "")
                if espeak_dir not in current_path:
                    os.environ["PATH"] = f"{espeak_dir};{current_path}"
                
                # Test if espeak command works
                try:
                    result = subprocess.run([espeak_exe, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print(f"eSpeak test successful: {result.stdout.strip()}")
                    else:
                        print(f"eSpeak test failed: {result.stderr}")
                except Exception as e:
                    print(f"eSpeak subprocess test failed: {e}")
        
        try:
            # Try to create a custom phonemizer for Windows
            if platform.system() == "Windows":
                espeak_exe = r"C:\Program Files\eSpeak NG\espeak.exe"
                if os.path.exists(espeak_exe):
                    # Create a custom phonemizer class that works with Windows eSpeak
                    self.phonemizer = WindowsEspeakPhonemizerWrapper(espeak_exe)
                    # Continue to set up text_cleaner and available_voices
                else:
                    # Try default eSpeak backend
                    self.phonemizer = phonemizer.backend.EspeakBackend(
                        language="en-us", preserve_punctuation=True, with_stress=True
                    )
            else:
                # Try default eSpeak backend for other platforms
                self.phonemizer = phonemizer.backend.EspeakBackend(
                    language="en-us", preserve_punctuation=True, with_stress=True
                )

        except RuntimeError as e:
            if "espeak not installed" in str(e):
                # For Windows, try to create a temporary espeak.exe symlink
                if platform.system() == "Windows":
                    try:
                        import tempfile
                        import shutil
                        
                        # Create a temporary directory
                        temp_dir = tempfile.mkdtemp()
                        espeak_ng_path = r"C:\Program Files\eSpeak NG\espeak-ng.exe"
                        temp_espeak_path = os.path.join(temp_dir, "espeak.exe")
                        
                        if os.path.exists(espeak_ng_path):
                            # Copy espeak-ng.exe to espeak.exe in temp directory
                            shutil.copy2(espeak_ng_path, temp_espeak_path)
                            
                            # Add temp directory to PATH
                            current_path = os.environ.get("PATH", "")
                            os.environ["PATH"] = f"{temp_dir};{current_path}"
                            
                            # Try again
                            self.phonemizer = phonemizer.backend.EspeakBackend(
                                language="en-us", preserve_punctuation=True, with_stress=True
                            )
                            return  # Success!
                    except Exception as ex:
                        print(f"Windows workaround failed: {ex}")
                
                # If all attempts fail, provide installation guidance
                raise RuntimeError(
                    "eSpeak is required for KittenTTS phonemization. "
                    "On Windows, please:\n"
                    "1. Ensure eSpeak-NG is installed from: https://github.com/espeak-ng/espeak-ng/releases\n"
                    "2. Run as Administrator: copy \"C:\\Program Files\\eSpeak NG\\espeak-ng.exe\" \"C:\\Program Files\\eSpeak NG\\espeak.exe\"\n"
                    "3. Or restart your terminal/IDE after installation\n"
                    "4. Or use Docker for easier setup"
                )
            else:
                raise e
        self.text_cleaner = TextCleaner()
        
        # Available voices
        self.available_voices = [
            'expr-voice-2-m', 'expr-voice-2-f', 'expr-voice-3-m', 'expr-voice-3-f', 
            'expr-voice-4-m', 'expr-voice-4-f', 'expr-voice-5-m', 'expr-voice-5-f'
        ]
    
    def _prepare_inputs(self, text: str, voice: str, speed: float = 1.0) -> dict:
        """Prepare ONNX model inputs from text and voice parameters."""
        if voice not in self.available_voices:
            raise ValueError(f"Voice '{voice}' not available. Choose from: {self.available_voices}")
        
        # Phonemize the input text
        phonemes_list = self.phonemizer.phonemize([text])
        
        # Process phonemes to get token IDs
        phonemes = basic_english_tokenize(phonemes_list[0])
        phonemes = ' '.join(phonemes)
        tokens = self.text_cleaner(phonemes)
        
        # Add start and end tokens
        tokens.insert(0, 0)
        tokens.append(0)
        
        input_ids = np.array([tokens], dtype=np.int64)
        ref_s = self.voices[voice]
        
        return {
            "input_ids": input_ids,
            "style": ref_s,
            "speed": np.array([speed], dtype=np.float32),
        }
    
    def generate(self, text: str, voice: str = "expr-voice-5-m", speed: float = 1.0) -> np.ndarray:
        """Synthesize speech from text.
        
        Args:
            text: Input text to synthesize
            voice: Voice to use for synthesis
            speed: Speech speed (1.0 = normal)
            
        Returns:
            Audio data as numpy array
        """
        onnx_inputs = self._prepare_inputs(text, voice, speed)
        
        outputs = self.session.run(None, onnx_inputs)
        
        # Trim audio
        audio = outputs[0][5000:-10000]

        return audio
    
    def generate_to_file(self, text: str, output_path: str, voice: str = "expr-voice-5-m", 
                          speed: float = 1.0, sample_rate: int = 24000) -> None:
        """Synthesize speech and save to file.
        
        Args:
            text: Input text to synthesize
            output_path: Path to save the audio file
            voice: Voice to use for synthesis
            speed: Speech speed (1.0 = normal)
            sample_rate: Audio sample rate
        """
        audio = self.generate(text, voice, speed)
        sf.write(output_path, audio, sample_rate)


class KittenTTS:
    """Main KittenTTS class for text-to-speech synthesis."""
    
    def __init__(self, model_name="KittenML/kitten-tts-nano-0.1", cache_dir=None):
        """Initialize KittenTTS with a model from Hugging Face.
        
        Args:
            model_name: Hugging Face repository ID or model name
            cache_dir: Directory to cache downloaded files
        """
        # Handle different model name formats
        if "/" not in model_name:
            # If just model name provided, assume it's from KittenML
            repo_id = f"KittenML/{model_name}"
        else:
            repo_id = model_name
            
        self.model = self._download_from_huggingface(repo_id=repo_id, cache_dir=cache_dir)
    
    def generate(self, text, voice="expr-voice-5-m", speed=1.0):
        """Generate audio from text.
        
        Args:
            text: Input text to synthesize
            voice: Voice to use for synthesis
            speed: Speech speed (1.0 = normal)
            
        Returns:
            Audio data as numpy array
        """
        return self.model.generate(text, voice=voice, speed=speed)
    
    def generate_to_file(self, text, output_path, voice="expr-voice-5-m", speed=1.0, sample_rate=24000):
        """Generate audio from text and save to file.
        
        Args:
            text: Input text to synthesize
            output_path: Path to save the audio file
            voice: Voice to use for synthesis
            speed: Speech speed (1.0 = normal)
            sample_rate: Audio sample rate
        """
        return self.model.generate_to_file(text, output_path, voice=voice, speed=speed, sample_rate=sample_rate)
    
    @property
    def available_voices(self):
        """Get list of available voices."""
        return self.model.available_voices

    def _download_from_huggingface(self, repo_id="KittenML/kitten-tts-nano-0.1", cache_dir=None):
        """Download model files from Hugging Face repository.
        
        Args:
            repo_id: Hugging Face repository ID
            cache_dir: Directory to cache downloaded files
            
        Returns:
            KittenTTSModel: Instantiated model ready for use
        """
        # Download config file first
        config_path = hf_hub_download(
            repo_id=repo_id,
            filename="config.json",
            cache_dir=cache_dir
        )
        
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)

        if config.get("type") != "ONNX1":
            raise ValueError("Unsupported model type.")

        # Download model and voices files based on config
        model_path = hf_hub_download(
            repo_id=repo_id,
            filename=config["model_file"],
            cache_dir=cache_dir
        )
        
        voices_path = hf_hub_download(
            repo_id=repo_id,
            filename=config["voices"],
            cache_dir=cache_dir
        )
        
        # Instantiate and return model
        model = KittenTTSModel(model_path=model_path, voices_path=voices_path)
        
        return model