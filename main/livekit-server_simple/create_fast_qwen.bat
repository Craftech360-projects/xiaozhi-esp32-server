@echo off
REM Create optimized qwen3-fast model without thinking mode

echo 🚀 Creating qwen3-fast model (optimized for speed)...

REM Create Modelfile
(
echo FROM qwen3:4b
echo.
echo # Disable thinking/reasoning tokens that slow down responses
echo PARAMETER stop "^<think^>"
echo PARAMETER stop "^</think^>"
echo PARAMETER stop "^<reasoning^>"
echo PARAMETER stop "^</reasoning^>"
echo PARAMETER stop "Let me think"
echo PARAMETER stop "I'm thinking"
echo.
echo # Speed optimizations
echo PARAMETER temperature 0.8
echo PARAMETER top_p 0.9
echo PARAMETER repeat_penalty 1.1
echo PARAMETER num_predict 512
echo.
echo # System prompt for fast, direct responses
echo SYSTEM You are Cheeko, a friendly AI assistant for kids. Respond quickly and naturally without showing your thinking process. Be concise, engaging, and direct. Never say "let me think" or show reasoning steps.
) > qwen3-fast.Modelfile

echo 📝 Modelfile created

REM Create the optimized model
echo ⏳ Creating qwen3-fast model (this may take a minute)...
ollama create qwen3-fast -f qwen3-fast.Modelfile

if %ERRORLEVEL% EQU 0 (
    echo ✅ qwen3-fast model created successfully!
    echo.
    echo 📝 Next steps:
    echo 1. Update your .env file:
    echo    LLM_MODEL=qwen3-fast
    echo    OLLAMA_MODEL=qwen3-fast
    echo.
    echo 2. Restart your agent:
    echo    python simple_main.py
    echo.
    echo 🧪 Test the model:
    echo    ollama run qwen3-fast "Hello, how are you?"
) else (
    echo ❌ Failed to create qwen3-fast model
    echo Make sure qwen3:4b is installed: ollama pull qwen3:4b
    exit /b 1
)

REM Cleanup
del qwen3-fast.Modelfile
echo 🧹 Cleaned up temporary files

pause
