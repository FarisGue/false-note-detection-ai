FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for audio processing.  The base slim
# image does not include codecs for reading MP3/OGG or handling MIDI via
# pretty_midi.  Installing ffmpeg and libsndfile ensures that libraries like
# librosa and soundfile can decode a wide range of audio formats.  We also
# clean up apt caches to keep the image lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose API port
EXPOSE 8000

# Run the API using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]