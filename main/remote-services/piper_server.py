#!/usr/bin/env python3
"""
Remote Piper TTS Server
Provides HTTP API for text-to-speech synthesis
"""
import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Configuration
PIPER_BINARY = os.getenv('PIPER_BINARY', 'piper')
PIPER_MODEL = os.getenv('PIPER_MODEL', './piper_models/en_US-amy-medium.onnx')
PIPER_VOICE = os.getenv('PIPER_VOICE', 'en_US-amy-medium')
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '22050'))

# Verify Piper is available
def check_piper():
    """Check if Piper is installed and accessible"""
    try:
        result = subprocess.run(
            [PIPER_BINARY, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        logger.info(f"✅ Piper found: {result.stdout.strip()}")
        return True
    except Exception as e:
        logger.error(f"❌ Piper not found: {e}")
        return False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    piper_available = check_piper()
    model_exists = os.path.exists(PIPER_MODEL)
    
    return jsonify({
        'status': 'ok' if (piper_available and model_exists) else 'error',
        'piper_available': piper_available,
        'model_exists': model_exists,
        'model': PIPER_MODEL,
        'voice': PIPER_VOICE,
        'sample_rate': SAMPLE_RATE
    })

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """
    Synthesize speech from text
    
    Accepts:
    - JSON with 'text' field
    
    Returns:
    - WAV audio file
    """
    try:
        # Get text
        if request.json and 'text' in request.json:
            text = request.json['text']
        elif request.form and 'text' in request.form:
            text = request.form['text']
        else:
            return jsonify({'error': 'No text provided'}), 400
        
        if not text or not text.strip():
            return jsonify({'error': 'Empty text provided'}), 400
        
        logger.info(f"Synthesizing: {text[:50]}...")
        
        # Create temp output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            output_file = f.name
        
        # Run Piper
        cmd = [
            PIPER_BINARY,
            '--model', PIPER_MODEL,
            '--output_file', output_file
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=text, timeout=30)
        
        if process.returncode != 0:
            logger.error(f"Piper error: {stderr}")
            return jsonify({'error': f'Piper failed: {stderr}'}), 500
        
        # Check if file was created
        if not os.path.exists(output_file):
            return jsonify({'error': 'Audio file not generated'}), 500
        
        file_size = os.path.getsize(output_file)
        logger.info(f"✅ Generated audio: {file_size} bytes")
        
        # Return audio file
        return send_file(
            output_file,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='speech.wav'
        )
    
    except subprocess.TimeoutExpired:
        logger.error("Piper timeout")
        return jsonify({'error': 'Synthesis timeout'}), 500
    
    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/info', methods=['GET'])
def info():
    """Get server information"""
    return jsonify({
        'piper_binary': PIPER_BINARY,
        'model': PIPER_MODEL,
        'voice': PIPER_VOICE,
        'sample_rate': SAMPLE_RATE,
        'model_exists': os.path.exists(PIPER_MODEL)
    })

if __name__ == '__main__':
    # Check Piper at startup
    logger.info("🚀 Starting Piper TTS Server")
    logger.info(f"   Model: {PIPER_MODEL}")
    logger.info(f"   Voice: {PIPER_VOICE}")
    logger.info(f"   Sample Rate: {SAMPLE_RATE}")
    
    if not check_piper():
        logger.error("❌ Piper not available. Please install Piper first.")
        logger.error("   Download from: https://github.com/rhasspy/piper/releases")
        sys.exit(1)
    
    if not os.path.exists(PIPER_MODEL):
        logger.error(f"❌ Model not found: {PIPER_MODEL}")
        logger.error("   Download models from: https://github.com/rhasspy/piper/releases")
        sys.exit(1)
    
    # Start server
    port = int(os.getenv('PORT', 8001))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"🌐 Server starting on http://{host}:{port}")
    logger.info(f"📝 Endpoints:")
    logger.info(f"   GET  /health - Health check")
    logger.info(f"   POST /synthesize - Synthesize speech")
    logger.info(f"   GET  /info - Server info")
    
    app.run(host=host, port=port, debug=False, threaded=True)
