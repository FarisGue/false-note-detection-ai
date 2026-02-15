# False Note Detection AI 🎵

AI-powered tool that detects false notes in musical performances by comparing audio recordings to a MIDI reference. Built with FastAPI, librosa, and Streamlit, it extracts pitch, aligns sequences using Dynamic Time Warping (DTW), and computes cents deviation to generate an accuracy score and identify out-of-tune segments.

## Features

- **Pitch Extraction**: Uses librosa's PYIN algorithm for robust pitch detection
- **DTW Alignment**: Dynamic Time Warping to handle tempo differences between performance and reference
- **Configurable Detection**: Adjustable threshold for error detection (in cents)
- **Multi-instrument MIDI Support**: Handles MIDI files with multiple instruments
- **Comprehensive Metrics**: 
  - Accuracy percentage
  - Mean and maximum cents deviation
  - Error timeline visualization
  - Detailed error indices
- **Modern UI**: Beautiful Streamlit interface with interactive visualizations
- **RESTful API**: FastAPI backend with automatic documentation
- **🤖 AI Recommendations**: Personalized recommendations using OpenRoute DeepSeek API to help musicians improve their playing

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the API Server

```bash
cd false-note-detection-ai
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/analysis/health`
- AI Recommendations: `http://localhost:8000/analysis/recommendations`

### Start the Streamlit Interface

```bash
cd false-note-detection-ai
streamlit run frontend/streamlit_app.py
```

The interface will be available at `http://localhost:8501`

## API Endpoints

### POST `/upload/`

Upload audio and MIDI files for analysis.

**Parameters:**
- `audio`: Audio file (WAV, MP3, FLAC, OGG, M4A)
- `reference`: MIDI reference file (MID, MIDI)
- `threshold_cents` (optional): Error detection threshold in cents (default: 40.0, range: 0-200)
- `ignore_silence` (optional): Ignore silent frames (default: true)

**Response:**
```json
{
  "total_frames": 5000,
  "correct_frames": 4800,
  "incorrect_frames": 200,
  "mean_cents": 25.5,
  "max_cents": 85.3,
  "accuracy_percent": 96.0,
  "error_indices": [100, 150, ...],
  "duration_seconds": 50.0,
  "threshold_cents": 40.0,
  "pitch_data": {...}
}
```

### POST `/analysis/recommendations`

Generate AI-powered recommendations for improving musical performance.

**Request Body:**
```json
{
  "analysis_result": {
    "total_frames": 5000,
    "accuracy_percent": 96.0,
    "mean_cents": 25.5,
    ...
  }
}
```

**Response:**
```json
{
  "recommendations": "Based on your performance analysis...",
  "success": true,
  "error_message": null
}
```

**Note:** The API key is pre-configured by default. You can override it using environment variables or a `.env` file.

## Configuration

Configuration can be set via environment variables or by editing `app/config.py`:

### Audio Processing
- `TARGET_SR`: Sampling rate for pitch timeline (default: 100.0 fps)
- `DEFAULT_THRESHOLD_CENTS`: Default error detection threshold (default: 40.0)
- `DEFAULT_IGNORE_SILENCE`: Ignore silence by default (default: true)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 50)
- `LOG_LEVEL`: Logging level (default: INFO)

### AI Recommendations
AI recommendations are enabled by default with a pre-configured API key. The configuration is loaded from:
1. Environment variables (highest priority)
2. `.env` file in the project root (if exists)
3. Default values in `app/config.py`

To customize the API key, you can:

**Option 1: Use .env file (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and update OPENROUTE_API_KEY with your own key
```

**Option 2: Set environment variable**
```bash
export OPENROUTE_API_KEY="your-api-key-here"
```
Or on Windows:
```powershell
$env:OPENROUTE_API_KEY="your-api-key-here"
```

**Configuration options:**
- `OPENROUTE_API_KEY`: Your OpenRoute API key (default: pre-configured)
- `OPENROUTE_API_URL`: API endpoint URL (default: `https://openrouter.ai/api/v1/chat/completions`)
- `DEEPSEEK_MODEL`: Model to use (default: `deepseek/deepseek-chat`)

**Note:** The `.env` file is automatically ignored by git for security reasons.

## How It Works

1. **Pitch Extraction**: Extracts fundamental frequency (f0) from audio using PYIN algorithm
2. **MIDI Processing**: Converts MIDI notes to frequency timeline at same sampling rate
3. **DTW Alignment**: Aligns audio and MIDI sequences to handle tempo variations
4. **Error Detection**: Compares aligned sequences and identifies frames where pitch deviation exceeds threshold
5. **Scoring**: Calculates accuracy, mean/max cents deviation, and error statistics
6. **AI Recommendations** (optional): Sends analysis results to OpenRoute DeepSeek API to generate personalized improvement suggestions

## Technologies

- **FastAPI**: Modern, fast web framework for building APIs
- **librosa**: Audio analysis library for pitch extraction
- **pretty_midi**: MIDI file parsing and manipulation
- **fastdtw**: Fast Dynamic Time Warping implementation
- **Streamlit**: Interactive web application framework
- **NumPy**: Numerical computing
- **Matplotlib**: Data visualization

## License

This project is open source and available for educational and research purposes.
