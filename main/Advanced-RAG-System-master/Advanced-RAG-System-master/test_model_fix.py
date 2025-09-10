# download_model_manually.py
import os
import requests
from pathlib import Path

def download_file(url, local_path):
    """Download a file from URL to local path"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"✅ Downloaded: {os.path.basename(local_path)}")

def download_all_minilm_model():
    """Download all required files for all-MiniLM-L6-v2 model"""
    
    # Create model directory
    model_dir = "./models/all-MiniLM-L6-v2"
    os.makedirs(model_dir, exist_ok=True)
    
    # List of files to download from HuggingFace
    files_to_download = [
        "config.json",
        "pytorch_model.bin", 
        "tokenizer_config.json",
        "tokenizer.json",
        "vocab.txt",
        "special_tokens_map.json"
    ]
    
    base_url = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/"
    
    print("📥 Downloading all-MiniLM-L6-v2 model files...")
    
    for filename in files_to_download:
        try:
            url = base_url + filename
            local_path = os.path.join(model_dir, filename)
            download_file(url, local_path)
        except Exception as e:
            print(f"⚠️ Could not download {filename}: {e}")
    
    print(f"✅ Model downloaded to: {model_dir}")
    return model_dir

if __name__ == "__main__":
    model_path = download_all_minilm_model()
