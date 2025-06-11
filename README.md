# 🎵 AudioFind - Shazam-Style Audio Recognition Engine

A powerful audio fingerprinting and recognition system built with Python and FastAPI that can identify songs from audio snippets, similar to Shazam.

![Audio Recognition Demo](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🔍 Audio Identification**: Upload an audio snippet and identify the song from your database
- **📁 Song Library Management**: Add songs to build your own recognition database
- **🌐 Web Interface**: Beautiful, responsive frontend for easy interaction
- **🚀 REST API**: Full-featured API for programmatic access
- **📊 Real-time Statistics**: Track your database size and performance metrics
- **🎯 High Accuracy**: Advanced fingerprinting algorithms for reliable recognition
- **🔄 Cross-platform**: Works on Windows, macOS, and Linux

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Audio Processing**: Librosa, NumPy, SciPy
- **Database**: SQLite with indexed fingerprints
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **API Documentation**: Automatic OpenAPI/Swagger docs

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/coderopp/audiofind.git
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the backend server**
   ```bash
   python app.py
   # Or using uvicorn directly:
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open the web interface**
   - Navigate to `frontend/index.html` in your browser
   - Or serve it with a local server:
   ```bash
   cd frontend
   python -m http.server 3000
   ```
   Then visit `http://localhost:3000`

## 📖 Usage

### Web Interface

1. **Adding Songs**: 
   - Go to the "Add Song" tab
   - Enter song title and artist
   - Upload an audio file (MP3, WAV, M4A, FLAC)
   - Click "Create Fingerprint"

2. **Identifying Songs**:
   - Go to the "Identify Song" tab
   - Upload an audio snippet
   - View the identification results with confidence scores

3. **Managing Library**:
   - Browse your song collection in the "Song Library" tab
   - Search through your songs
   - View database statistics

### API Usage

The backend provides a full REST API. Here are the main endpoints:

#### Add a song to the database
```bash
curl -X POST "http://localhost:8000/fingerprint" \
  -F "audio=@song.mp3" \
  -F "title=Song Title" \
  -F "artist=Artist Name"
```

#### Identify a song
```bash
curl -X POST "http://localhost:8000/identify" \
  -F "audio=@snippet.mp3"
```

#### Get all songs
```bash
curl "http://localhost:8000/songs"
```

### Python Client

Use the included client for programmatic access:

```python
from client_test import AudioFingerprintClient

client = AudioFingerprintClient('http://localhost:8000')

# Add a song
result = client.fingerprint_song('path/to/song.mp3', 'Song Title', 'Artist')

# Identify a song
result = client.identify_song('path/to/snippet.mp3')
```

## 🧪 Testing

Run the test client to verify everything works:

```bash
python client_test.py
```

Choose option 1 for automated testing or option 2 for interactive mode.

## 📁 Project Structure

```
├── app.py                 # FastAPI backend server
├── client_test.py        # Python client for testing
├── requirements.txt      # Python dependencies
├── fingerprints.db      # SQLite database (created automatically)
├── audio_samples/       # Directory for sample audio files
├── frontend/            # Web interface
│   ├── index.html      # Main HTML file
│   ├── style.css       # Styling
│   └── script.js       # JavaScript functionality
└── README.md           # This file
```

## 🔧 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/songs` | List all songs |
| POST | `/fingerprint` | Add song to database |
| POST | `/identify` | Identify song from audio |
| GET | `/stats` | Database statistics |
| POST | `/reset` | Reset database |

## 🎯 How It Works

The audio recognition engine uses several key components:

1. **Audio Preprocessing**: Convert audio to a standard format and extract features
2. **Spectrogram Analysis**: Generate mel-scaled spectrograms for frequency analysis
3. **Peak Detection**: Identify significant peaks in the frequency domain
4. **Fingerprint Generation**: Create unique hashes from peak relationships
5. **Database Storage**: Store fingerprints with time offsets for quick lookup
6. **Matching Algorithm**: Compare query fingerprints against the database
7. **Confidence Scoring**: Calculate match confidence based on coherent time alignments

## 🔒 Security Notes

- The current CORS configuration allows `localhost:3000` only
- For production deployment, configure proper CORS origins
- Consider implementing authentication for write operations
- Validate file uploads and implement size limits

## 🚀 Deployment

### Local Production
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the Shazam audio recognition algorithm
- Built with the amazing [Librosa](https://librosa.org/) library
- FastAPI for the excellent web framework
- The open-source community for various tools and libraries

## 📞 Support

If you encounter any issues or have questions:
1. Check the [API documentation](http://localhost:8000/docs) when running
2. Run the test client to verify setup
3. Open an issue on GitHub

---

**Made with ❤️ for music lovers and developers**