#!/bin/sh
# This script is used to automatically download the required files for this project and create the necessary directories.
# Requirements (otherwise it will not work):
# 1. Please make sure your environment can access GitHub, otherwise the script cannot be downloaded.
#
# Detect operating system type
case "$(uname -s)" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    CYGWIN*)    OS=Windows;;
    MINGW*)     OS=Windows;;
    MSYS*)      OS=Windows;;
    *)          OS=UNKNOWN;;
esac

# Set color (Windows CMD does not support, but does not affect usage)
if [ "$OS" = "Windows" ]; then
    GREEN=""
    RED=""
    NC=""
else
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    NC='\033[0m'
fi

echo "${GREEN}Starting Xiaozhi server installation...${NC}"

# Create necessary directories
echo "Creating directory structure..."
mkdir -p xiaozhi-server/data xiaozhi-server/models/SenseVoiceSmall
cd xiaozhi-server || exit

# Select download command based on OS
if [ "$OS" = "Windows" ]; then
    DOWNLOAD_CMD="curl -L -o"
    if ! command -v curl >/dev/null 2>&1; then
        DOWNLOAD_CMD="powershell -Command Invoke-WebRequest -Uri"
        DOWNLOAD_CMD_SUFFIX="-OutFile"
    fi
else
    if command -v curl >/dev/null 2>&1; then
        DOWNLOAD_CMD="curl -L -o"
    elif command -v wget >/dev/null 2>&1; then
        DOWNLOAD_CMD="wget -O"
    else
        echo "${RED}Error: curl or wget is required${NC}"
        exit 1
    fi
fi

# Download speech recognition model
if [ -f "models/SenseVoiceSmall/model.pt" ]; then
    echo "Speech recognition model already exists, skipping download..."
else
    echo "Downloading speech recognition model..."
    if [ "$DOWNLOAD_CMD" = "powershell -Command Invoke-WebRequest -Uri" ]; then
        eval "$DOWNLOAD_CMD 'https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt' $DOWNLOAD_CMD_SUFFIX 'models/SenseVoiceSmall/model.pt'"
    else
        eval "$DOWNLOAD_CMD 'models/SenseVoiceSmall/model.pt' 'https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt'"
    fi
fi

if [ $? -ne 0 ]; then
    echo "${RED}Model download failed. Please manually download from the following addresses:${NC}"
    echo "1. https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt"
    echo "2. Baidu Netdisk: https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg (Extraction code: qvna)"
    echo "After downloading, please place the file at models/SenseVoiceSmall/model.pt"
fi

# Download configuration files
echo "Downloading configuration files..."
if [ ! -f "docker-compose.yml" ]; then
    echo "Downloading docker-compose.yml..."
    if [ "$DOWNLOAD_CMD" = "powershell -Command Invoke-WebRequest -Uri" ]; then
        eval "$DOWNLOAD_CMD 'https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/docker-compose.yml' $DOWNLOAD_CMD_SUFFIX 'docker-compose.yml'"
    else
        eval "$DOWNLOAD_CMD 'docker-compose.yml' 'https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/docker-compose.yml'"
    fi
else
    echo "docker-compose.yml already exists, skipping download..."
fi

if [ ! -f "data/.config.yaml" ]; then
    echo "Downloading config.yaml..."
    if [ "$DOWNLOAD_CMD" = "powershell -Command Invoke-WebRequest -Uri" ]; then
        eval "$DOWNLOAD_CMD 'https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/config.yaml' $DOWNLOAD_CMD_SUFFIX 'data/.config.yaml'"
    else
        eval "$DOWNLOAD_CMD 'data/.config.yaml' 'https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/config.yaml'"
    fi
else
    echo "data/.config.yaml already exists, skipping download..."
fi

# Check if files exist
echo "Checking file integrity..."
FILES_TO_CHECK="docker-compose.yml data/.config.yaml models/SenseVoiceSmall/model.pt"
ALL_FILES_EXIST=true

for FILE in $FILES_TO_CHECK; do
    if [ ! -f "$FILE" ]; then
        echo "${RED}Error: $FILE does not exist${NC}"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo "${RED}Some files failed to download. Please check the above error messages and manually download the missing files.${NC}"
    exit 1
fi

echo "${GREEN}File download completed!${NC}"
echo "Please edit the data/.config.yaml file to configure your API keys."
echo "After configuration, run the following command to start the service:"
echo "${GREEN}docker-compose up -d${NC}"
echo "To view logs, run:"
echo "${GREEN}docker logs -f xiaozhi-esp32-server${NC}"

# Remind user to edit configuration file
echo "\n${RED}Important Notice:${NC}"
echo "1. Please make sure to edit the data/.config.yaml file and configure the required API keys"
echo "2. Especially the keys for ChatGLM and mem0ai must be configured"
echo "3. Start the docker service only after configuration is complete"
