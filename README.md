# Shazam-Style Audio Recognition Engine

A Python-based audio fingerprinting system that can identify songs from short audio clips, similar to how Shazam works. This project implements audio fingerprinting using spectral peak analysis and hash-based matching.

## Features

- **Audio Fingerprinting**: Extract unique audio fingerprints from songs using spectral analysis
- **Fast Recognition**: Identify songs from short audio clips (even a few seconds)
- **Web Interface**: Simple HTML frontend for easy interaction
- **REST API**: FastAPI backend with endpoints for fingerprinting and identification
- **Database Storage**: SQLite database for storing song fingerprints
- **Multiple Audio Formats**: Support for MP3, WAV, M4A, and FLAC files

## How It Works

1. **Fingerprinting**: The system analyzes audio files to extract spectral peaks and creates unique hash fingerprints
2. **Storage**: Fingerprints are stored in a SQLite database along with song metadata
3. **Recognition**: When identifying a song, it extracts fingerprints from the audio clip and matches them against the database
4. **Matching**: Uses combinatorial hashing to find coherent matches and calculate confidence scores

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Shazam-style-audio-recognition-engine.git
cd Shazam-style-audio-recognition-engine
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

Start the FastAPI server:
```bash
python app.py
```

The server will start on `http://localhost:8000`

### Web Interface

Open your browser and go to `http://localhost:8000` to access the web interface where you can:
- Upload audio files to add to the database
- Upload audio clips to identify songs

### API Endpoints

- `GET /` - Web interface
- `POST /fingerprint` - Add a song to the database
- `POST /identify` - Identify a song from an audio clip
- `GET /songs` - List all songs in the database
- `GET /stats` - Get database statistics
- `GET /health` - Health check
- `POST /reset` - Reset the database

### Command Line Testing

Use the included client test script:
```bash
python client_test.py
```

This script provides both automated testing and an interactive mode for testing the system.

## Project Structure

```
├── app.py                 # FastAPI backend server
├── client_test.py         # Test client with interactive mode
├── requirements.txt       # Python dependencies
├── fingerprints.db       # SQLite database (created automatically)
├── frontend/             # Web interface files
│   ├── index.html
│   ├── script.js
│   └── style.css
└── audio_samples/        # Directory for test audio files
```

## API Reference

### Fingerprint a Song
```http
POST /fingerprint
Content-Type: multipart/form-data

Parameters:
- audio: Audio file (MP3, WAV, M4A, FLAC)
- title: Song title (optional)
- artist: Artist name (optional)
```

### Identify a Song
```http
POST /identify
Content-Type: multipart/form-data

Parameters:
- audio: Audio clip to identify
```

### Get All Songs
```http
GET /songs
```

### Database Statistics
```http
GET /stats
```

## Technical Details

### Audio Processing
- Uses librosa for audio analysis
- Extracts spectral peaks using STFT (Short-Time Fourier Transform)
- Implements constellation mapping for robust fingerprint generation

### Fingerprinting Algorithm
- Converts audio to mono and resamples to 22.05 kHz
- Applies STFT with specific window parameters
- Identifies spectral peaks above threshold
- Creates combinatorial hashes from peak pairs
- Stores hashes with time offsets for temporal matching

### Matching Process
- Extracts fingerprints from query audio
- Performs database lookup for matching hashes
- Calculates time differences for coherent matching
- Returns best match with confidence score

## Dependencies

- **FastAPI**: Web framework for the API
- **librosa**: Audio analysis and processing
- **numpy**: Numerical computations
- **scipy**: Scientific computing
- **soundfile**: Audio file I/O
- **uvicorn**: ASGI server

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Inspired by the Shazam audio recognition algorithm
- Built using librosa for robust audio processing
- FastAPI for the modern web framework

## Future Enhancements

- [ ] Support for larger databases with optimized indexing
- [ ] Real-time audio recognition from microphone input
- [ ] Advanced noise reduction and audio preprocessing
- [ ] Machine learning-based confidence scoring
- [ ] Support for audio streaming protocols
- [ ] Multi-threaded processing for better performance