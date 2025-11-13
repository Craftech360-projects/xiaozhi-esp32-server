#!/bin/bash
# Setup script for remote PC (Linux/Mac)

echo "🚀 Setting up Remote Whisper + Piper Servers"
echo "=============================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Download Piper if not exists
if ! command -v piper &> /dev/null; then
    echo "📥 Downloading Piper..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PIPER_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PIPER_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz"
    else
        echo "⚠️  Please download Piper manually from: https://github.com/rhasspy/piper/releases"
        PIPER_URL=""
    fi
    
    if [ ! -z "$PIPER_URL" ]; then
        wget $PIPER_URL -O piper.tar.gz
        tar -xzf piper.tar.gz
        chmod +x piper/piper
        export PATH="$PWD/piper:$PATH"
        echo "✅ Piper installed"
    fi
fi

# Download Piper model
echo "📥 Downloading Piper model..."
mkdir -p piper_models
cd piper_models

if [ ! -f "en_US-amy-medium.onnx" ]; then
    wget https://github.com/rhasspy/piper/releases/download/v0.0.2/en_US-amy-medium.onnx
    wget https://github.com/rhasspy/piper/releases/download/v0.0.2/en_US-amy-medium.onnx.json
    echo "✅ Piper model downloaded"
else
    echo "✅ Piper model already exists"
fi

cd ..

# Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
# Whisper Server Configuration
WHISPER_MODEL=base.en
HOST=0.0.0.0
WHISPER_PORT=8000

# Piper Server Configuration
PIPER_MODEL=./piper_models/en_US-amy-medium.onnx
PIPER_VOICE=en_US-amy-medium
SAMPLE_RATE=22050
PIPER_PORT=8001
EOF

echo "✅ .env file created"

# Create start scripts
echo "📝 Creating start scripts..."

cat > start_whisper.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PORT=8000
python whisper_server.py
EOF

cat > start_piper.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PORT=8001
python piper_server.py
EOF

cat > start_all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting all services..."
./start_whisper.sh &
./start_piper.sh &
echo "✅ Services started"
echo "   Whisper: http://0.0.0.0:8000"
echo "   Piper:   http://0.0.0.0:8001"
wait
EOF

chmod +x start_whisper.sh start_piper.sh start_all.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Start Whisper server: ./start_whisper.sh"
echo "2. Start Piper server:   ./start_piper.sh"
echo "3. Or start both:        ./start_all.sh"
echo ""
echo "🧪 Test endpoints:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8001/health"
