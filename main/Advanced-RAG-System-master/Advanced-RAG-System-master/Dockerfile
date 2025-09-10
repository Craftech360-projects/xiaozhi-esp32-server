# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port (optional, e.g., for FastAPI or Streamlit)
EXPOSE 8000

# Default command (runs demo.py, change as needed)
CMD ["streamlit","run", "demo.py"]
