#!/usr/bin/env python3
"""
Remote Whisper STT Server
Provides HTTP API for speech-to-text transcription
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Configuration
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base.en')
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Global model instance (loaded once)
model = None

def load_model():
    """Load Whisper model once at startup"""
    global model
    if model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL} on {DEVICE}")
        model = whisper.load_model(WHISPER_MODEL, device=DEVICE)
        logger.info(f"✅ Whisper model loaded successfully")
    return model

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'model': WHISPER_MODEL,
        'device': DEVICE,
        'model_loaded': model is not None
    })

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio file
    
    Accepts:
    - multipart/form-data with 'audio' file
    - application/json with 'audio_data' base64 encoded
    
    Returns:
    - JSON with 'text' field
    """
    try:
        # Get audio file
        if 'audio' in request.files:
            audio_file = request.files['audio']
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                audio_path = f.name
                audio_file.save(audio_path)
        
        elif request.json and 'audio_data' in request.json:
            # Base64 encoded audio
            import base64
            audio_data = base64.b64decode(request.json['audio_data'])
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                audio_path = f.name
                f.write(audio_data)
        
        else:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Load model if not loaded
        whisper_model = load_model()
        
        # Transcribe
        logger.info(f"Transcribing audio: {audio_path}")
        result = whisper_model.transcribe(
            audio_path,
            language='en',
            fp16=(DEVICE == 'cuda')
        )
        
        text = result['text'].strip()
        logger.info(f"Transcription result: {text}")
        
        # Cleanup
        try:
            os.unlink(audio_path)
        except:
            pass
        
        return jsonify({
            'text': text,
            'language': result.get('language', 'en')
        })
    
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/info', methods=['GET'])
def info():
    """Get server information"""
    return jsonify({
        'model': WHISPER_MODEL,
        'device': DEVICE,
        'cuda_available': torch.cuda.is_available(),
        'model_loaded': model is not None
    })

if __name__ == '__main__':
    # Preload model at startup
    logger.info("🚀 Starting Whisper STT Server")
    logger.info(f"   Model: {WHISPER_MODEL}")
    logger.info(f"   Device: {DEVICE}")
    
    load_model()
    
    # Start server
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"🌐 Server starting on http://{host}:{port}")
    logger.info(f"📝 Endpoints:")
    logger.info(f"   GET  /health - Health check")
    logger.info(f"   POST /transcribe - Transcribe audio")
    logger.info(f"   GET  /info - Server info")
    
    app.run(host=host, port=port, debug=False, threaded=True)
