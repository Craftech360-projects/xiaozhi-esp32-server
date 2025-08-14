# Installing eSpeak-NG on Windows for KittenTTS

KittenTTS requires eSpeak-NG for text phonemization. Here are several ways to install it on Windows:

## Method 1: Direct Download (Recommended)

1. **Download eSpeak-NG**:
   - Go to: https://github.com/espeak-ng/espeak-ng/releases
   - Download the latest Windows installer (`.msi` file)
   - Example: `espeak-ng-X.XX.X-x64.msi`

2. **Install**:
   - Run the downloaded `.msi` file
   - Follow the installation wizard
   - Choose default installation path (usually `C:\Program Files\eSpeak NG\`)

3. **Verify Installation**:
   ```bash
   espeak --version
   ```

## Method 2: Using Conda (If you have Anaconda/Miniconda)

```bash
conda install -c conda-forge espeak-ng
```

## Method 3: Using Windows Package Manager (winget)

```bash
winget install espeak-ng
```

## Method 4: Using Chocolatey (If you have Chocolatey)

```bash
choco install espeak
```

## After Installation

1. **Restart your terminal/command prompt**
2. **Test eSpeak**:
   ```bash
   espeak "Hello world"
   ```
3. **Run KittenTTS installation**:
   ```bash
   cd main/xiaozhi-server
   python install_kittentts.py
   ```

## Troubleshooting

### eSpeak not found in PATH
If you get "espeak not found" errors:

1. **Add to PATH manually**:
   - Open System Properties → Advanced → Environment Variables
   - Add eSpeak installation directory to PATH
   - Usually: `C:\Program Files\eSpeak NG\`

2. **Restart terminal** and try again

### Permission Issues
- Run terminal as Administrator when installing
- Or use `--user` flag with pip commands

### Alternative: Use Docker
If you can't install eSpeak directly, consider using Docker:
```bash
docker run -it python:3.9 bash
# Then install eSpeak inside container
apt-get update && apt-get install -y espeak-ng
```

## Verification

After successful installation, you should be able to run:
```bash
cd main/xiaozhi-server
python test_kittentts.py
```

Without any "espeak not installed" errors.