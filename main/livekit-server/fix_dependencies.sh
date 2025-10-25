#!/bin/bash
# Fix sentence-transformers and PyTorch dependencies

echo "🔧 Fixing sentence-transformers dependencies..."

# Uninstall conflicting packages
pip3 uninstall -y torch torchvision sentence-transformers

# Reinstall with compatible versions
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Reinstall sentence-transformers
pip3 install sentence-transformers

echo "✅ Dependencies fixed! Please restart your LiveKit server."
