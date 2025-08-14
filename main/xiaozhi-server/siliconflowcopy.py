import requests
from cosyvoice import CosyVoice

# --------------------------
# 1. GET SAMPLE FROM SILICONFLOW
# --------------------------
API_KEY = "sk-bhwcvtzebmaewxsiuwaqlapaownasowwqinoxibiawexuecp"
VOICE_NAME = "diana"  # alex, benjamin, charles, david, anna, bella, claire, diana
SAMPLE_TEXT = "This is a reference sample for cloning Bella's voice."

siliconflow_url = "https://api.siliconflow.cn/v1/audio/speech"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": "FunAudioLLM/CosyVoice2-0.5B",
    "voice": VOICE_NAME,
    "input": SAMPLE_TEXT
}

print(f"[SiliconFlow] Generating sample voice for {VOICE_NAME}...")
response = requests.post(siliconflow_url, json=payload, headers=headers)
if response.status_code != 200:
    raise RuntimeError(f"SiliconFlow API error: {response.status_code} - {response.text}")

with open("voice_sample.wav", "wb") as f:
    f.write(response.content)
print("[SiliconFlow] Sample saved as voice_sample.wav")

# --------------------------
# 2. RUN COSYVOICE LOCALLY
# --------------------------
print("[CosyVoice] Loading local CosyVoice model...")
cosy = CosyVoice("FunAudioLLM/CosyVoice2-0.5B")  # make sure you have this model locally

OUTPUT_TEXT = "Hi there! Now I am speaking with Bella's voice, cloned locally."
print("[CosyVoice] Generating cloned voice output...")
output_audio = cosy.tts(
    text=OUTPUT_TEXT,
    speaker_prompt="voice_sample.wav"  # reference voice from SiliconFlow
)

cosy.save(output_audio, "bella_clone.wav")
print("[Done] Saved cloned output as bella_clone.wav")
