#!/bin/bash
# Create optimized qwen3-fast model without thinking mode

echo "🚀 Creating qwen3-fast model (optimized for speed)..."

# Create Modelfile
cat > qwen3-fast.Modelfile << 'EOF'
FROM qwen3:4b

# Disable thinking/reasoning tokens that slow down responses
PARAMETER stop "<think>"
PARAMETER stop "</think>"
PARAMETER stop "<reasoning>"
PARAMETER stop "</reasoning>"
PARAMETER stop "Let me think"
PARAMETER stop "I'm thinking"

# Speed optimizations
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 512

# System prompt for fast, direct responses
SYSTEM You are Cheeko, a friendly AI assistant for kids. Respond quickly and naturally without showing your thinking process. Be concise, engaging, and direct. Never say "let me think" or show reasoning steps.
EOF

echo "📝 Modelfile created"

# Create the optimized model
echo "⏳ Creating qwen3-fast model (this may take a minute)..."
ollama create qwen3-fast -f qwen3-fast.Modelfile

if [ $? -eq 0 ]; then
    echo "✅ qwen3-fast model created successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Update your .env file:"
    echo "   LLM_MODEL=qwen3-fast"
    echo "   OLLAMA_MODEL=qwen3-fast"
    echo ""
    echo "2. Restart your agent:"
    echo "   python simple_main.py"
    echo ""
    echo "🧪 Test the model:"
    echo "   ollama run qwen3-fast \"Hello, how are you?\""
else
    echo "❌ Failed to create qwen3-fast model"
    echo "Make sure qwen3:4b is installed: ollama pull qwen3:4b"
    exit 1
fi

# Cleanup
rm qwen3-fast.Modelfile
echo "🧹 Cleaned up temporary files"
