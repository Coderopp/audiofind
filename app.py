# Audio Fingerprinting Backend
# Requirements: pip install fastapi uvicorn python-multipart librosa numpy scipy
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import librosa
import numpy as np
from scipy import signal
import sqlite3
import hashlib
import json
import os
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class APIInfo(BaseModel):
    message: str
    status: str
    endpoints: Dict[str, str]
    usage: Dict[str, str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str

class SongInfo(BaseModel):
    id: int
    filename: str
    title: Optional[str]
    artist: Optional[str]
    duration: Optional[float]
    created_at: Optional[str]

class SongsResponse(BaseModel):
    songs: List[SongInfo]
    count: int

class FingerprintStats(BaseModel):
    duration: float
    peaks_found: int
    hashes_generated: int

class FingerprintResponse(BaseModel):
    success: bool
    song_id: int
    message: str
    stats: FingerprintStats

class MatchDetails(BaseModel):
    coherent_matches: int
    total_matches: int
    song_offset: float

class QueryStats(BaseModel):
    peaks_found: int
    hashes_generated: int

class MatchInfo(BaseModel):
    song_info: SongInfo
    confidence: float
    coherent_matches: int
    total_matches: int
    song_offset: float

class IdentifyResponse(BaseModel):
    success: bool
    match_found: bool
    song: Optional[SongInfo] = None
    confidence: Optional[float] = None
    match_details: Optional[MatchDetails] = None
    query_stats: QueryStats
    all_matches: List[MatchInfo] = []
    message: Optional[str] = None

class DatabaseStats(BaseModel):
    total_songs: int
    total_fingerprints: int
    avg_fingerprints_per_song: float

class StatsResponse(BaseModel):
    database_stats: DatabaseStats

class ResetResponse(BaseModel):
    success: bool
    message: str

# Audio Fingerprinting logic
class AudioFingerprinter:
    def __init__(self, db_path='fingerprints.db'):
        self.db_path = db_path
        self.init_database()
        
        # Fingerprinting parameters
        self.sample_rate = 22050
        self.n_fft = 2048
        self.hop_length = 512
        self.n_mels = 128
        
        # Peak detection parameters
        self.peak_threshold = 0.1
        self.min_time_delta = 0.1  # seconds
        self.max_time_delta = 2.0  # seconds
        self.fanout = 5  # number of target peaks per anchor
        
    def init_database(self):
        """Initialize SQLite database for storing fingerprints"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Songs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    title TEXT,
                    artist TEXT,
                    duration REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Fingerprints table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id INTEGER,
                    hash_value TEXT NOT NULL,
                    time_offset REAL NOT NULL,
                    FOREIGN KEY (song_id) REFERENCES songs (id)
                )
            ''')
            
            # Create index separately for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints (hash_value)
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def load_audio(self, file_path):
        """Load audio file and return audio data and sample rate"""
        try:
            # Validate file extension
            valid_extensions = ['.wav', '.mp3', '.m4a', '.flac']
            if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
                raise ValueError("Unsupported audio format")
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            return audio, sr
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            raise
    
    def compute_spectrogram(self, audio):
        """Compute mel-scaled spectrogram"""
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(stft)
        
        mel_spec = librosa.feature.melspectrogram(
            S=magnitude**2, 
            sr=self.sample_rate,
            n_mels=self.n_mels
        )
        
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        return mel_spec_db
    
    def find_peaks(self, spectrogram):
        """Find peaks in the spectrogram using local maxima detection"""
        peaks = []
        freq_bands = [(0, 10), (10, 20), (20, 40), (40, 80), (80, 128)]
        
        for time_idx in range(spectrogram.shape[1]):
            for freq_start, freq_end in freq_bands:
                band = spectrogram[freq_start:freq_end, time_idx]
                
                if len(band) == 0:
                    continue
                
                max_idx = np.argmax(band)
                max_value = band[max_idx]
                
                if max_value > self.peak_threshold:
                    is_peak = True
                    for t_offset in [-1, 1]:
                        if (0 <= time_idx + t_offset < spectrogram.shape[1] and 
                            spectrogram[freq_start + max_idx, time_idx + t_offset] > max_value):
                            is_peak = False
                            break
                    
                    if is_peak:
                        time_sec = time_idx * self.hop_length / self.sample_rate
                        freq_idx = freq_start + max_idx
                        peaks.append({
                            'time': time_sec,
                            'frequency': freq_idx,
                            'magnitude': max_value
                        })
        
        peaks.sort(key=lambda x: x['time'])
        logger.info(f"Found {len(peaks)} peaks")
        return peaks
    
    def generate_hashes(self, peaks):
        """Generate fingerprint hashes from peaks"""
        hashes = []
        
        for i, anchor in enumerate(peaks):
            targets = []
            for j in range(i + 1, len(peaks)):
                target = peaks[j]
                time_delta = target['time'] - anchor['time']
                
                if time_delta < self.min_time_delta:
                    continue
                if time_delta > self.max_time_delta:
                    break
                
                targets.append((j, target, time_delta))
                
                if len(targets) >= self.fanout:
                    break
            
            for _, target, time_delta in targets:
                hash_input = f"{anchor['frequency']}_{target['frequency']}_{int(time_delta * 1000)}"
                hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
                hashes.append({
                    'hash': hash_value,
                    'time_offset': anchor['time']
                })
        
        logger.info(f"Generated {len(hashes)} hashes")
        return hashes
    
    def fingerprint_audio(self, audio):
        """Generate fingerprint for audio data"""
        spectrogram = self.compute_spectrogram(audio)
        peaks = self.find_peaks(spectrogram)
        hashes = self.generate_hashes(peaks)
        
        return {
            'peaks': peaks,
            'hashes': hashes,
            'spectrogram_shape': spectrogram.shape
        }
    
    def store_fingerprint(self, filename, title, artist, fingerprint, duration):
        """Store fingerprint in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert or update song and get song_id
            cursor.execute('''
                INSERT OR REPLACE INTO songs (filename, title, artist, duration)
                VALUES (?, ?, ?, ?)
            ''', (filename, title, artist, duration))
            
            # Fetch the song_id
            cursor.execute('SELECT id FROM songs WHERE filename = ?', (filename,))
            song_id = cursor.fetchone()[0]
            
            # Delete existing fingerprints for this song
            cursor.execute('DELETE FROM fingerprints WHERE song_id = ?', (song_id,))
            
            # Insert fingerprints
            for hash_data in fingerprint['hashes']:
                cursor.execute('''
                    INSERT INTO fingerprints (song_id, hash_value, time_offset)
                    VALUES (?, ?, ?)
                ''', (song_id, hash_data['hash'], hash_data['time_offset']))
            
            conn.commit()
            logger.info(f"Stored fingerprint for song ID {song_id}")
            return song_id
    
    def match_fingerprint(self, query_fingerprint):
        """Match query fingerprint against database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            matches = {}
            
            for hash_data in query_fingerprint['hashes']:
                query_hash = hash_data['hash']
                query_time = hash_data['time_offset']
                
                cursor.execute('''
                    SELECT f.song_id, f.time_offset, s.title, s.artist, s.filename
                    FROM fingerprints f
                    JOIN songs s ON f.song_id = s.id
                    WHERE f.hash_value = ?
                ''', (query_hash,))
                
                results = cursor.fetchall()
                
                for song_id, db_time, title, artist, filename in results:
                    if song_id not in matches:
                        matches[song_id] = {
                            'song_info': {'id': song_id, 'title': title, 'artist': artist, 'filename': filename},
                            'time_pairs': []
                        }
                    matches[song_id]['time_pairs'].append((query_time, db_time))
        
        best_matches = []
        
        for song_id, match_data in matches.items():
            if len(match_data['time_pairs']) < 3:
                continue
            
            time_deltas = [db_time - query_time for query_time, db_time in match_data['time_pairs']]
            delta_counts = {}
            for delta in time_deltas:
                rounded_delta = round(delta, 1)
                delta_counts[rounded_delta] = delta_counts.get(rounded_delta, 0) + 1
            
            if not delta_counts:
                continue
            
            best_delta = max(delta_counts, key=delta_counts.get)
            coherent_matches = delta_counts[best_delta]
            total_matches = len(match_data['time_pairs'])
            coherence_score = coherent_matches / total_matches
            match_strength = coherent_matches / len(query_fingerprint['hashes'])
            confidence = (coherence_score * 0.6 + match_strength * 0.4) * 100
            
            best_matches.append({
                'song_info': match_data['song_info'],
                'confidence': confidence,
                'coherent_matches': coherent_matches,
                'total_matches': total_matches,
                'song_offset': best_delta
            })
        
        best_matches.sort(key=lambda x: x['confidence'], reverse=True)
        logger.info(f"Found {len(best_matches)} potential matches")
        return best_matches

# Initialize fingerprinter
fingerprinter = AudioFingerprinter()

# Create FastAPI app
app = FastAPI(
    title="Audio Fingerprinting API",
    description="A Shazam-style audio recognition engine that can fingerprint and identify songs",
    version="1.0.0"
)

# Add CORS middleware (restrict to specific origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Example: restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=APIInfo)
async def home():
    """Root endpoint with API information"""
    return APIInfo(
        message="Audio Fingerprinting API",
        status="running",
        endpoints={
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /songs": "List all songs",
            "POST /fingerprint": "Add song to database (requires audio file)",
            "POST /identify": "Identify song from audio (requires audio file)",
            "GET /stats": "Database statistics",
            "POST /reset": "Reset database",
            "GET /docs": "Interactive API documentation"
        },
        usage={
            "fingerprint": "Send POST with 'audio' file + optional 'title' and 'artist' form data",
            "identify": "Send POST with 'audio' file to identify"
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.get("/songs", response_model=SongsResponse)
async def get_songs():
    """Get all songs in database"""
    try:
        with sqlite3.connect(fingerprinter.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, filename, title, artist, duration, created_at FROM songs')
            songs = [SongInfo(id=row[0], filename=row[1], title=row[2], artist=row[3], duration=row[4], created_at=row[5]) 
                     for row in cursor.fetchall()]
        
        return SongsResponse(songs=songs, count=len(songs))
    except Exception as e:
        logger.error(f"Error getting songs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fingerprint", response_model=FingerprintResponse)
async def fingerprint_song(
    audio: UploadFile = File(..., description="Audio file to fingerprint"),
    title: str = Form("Unknown", description="Song title"),
    artist: str = Form("Unknown", description="Artist name")
):
    """Fingerprint and store a song"""
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as temp_file:
            temp_file.write(await audio.read())
            temp_path = temp_file.name
        
        try:
            audio_data, sr = fingerprinter.load_audio(temp_path)
            duration = len(audio_data) / sr
            fingerprint = fingerprinter.fingerprint_audio(audio_data)
            song_id = fingerprinter.store_fingerprint(audio.filename, title, artist, fingerprint, duration)
            
            return FingerprintResponse(
                success=True,
                song_id=song_id,
                message=f'Successfully fingerprinted "{title}" by {artist}',
                stats=FingerprintStats(
                    duration=duration,
                    peaks_found=len(fingerprint['peaks']),
                    hashes_generated=len(fingerprint['hashes'])
                )
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"Error fingerprinting song: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/identify", response_model=IdentifyResponse)
async def identify_song(
    audio: UploadFile = File(..., description="Audio file to identify")
):
    """Identify a song from audio snippet"""
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as temp_file:
            temp_file.write(await audio.read())
            temp_path = temp_file.name
        
        try:
            audio_data, sr = fingerprinter.load_audio(temp_path)
            query_fingerprint = fingerprinter.fingerprint_audio(audio_data)
            matches = fingerprinter.match_fingerprint(query_fingerprint)
            
            if not matches:
                return IdentifyResponse(
                    success=True,
                    match_found=False,
                    query_stats=QueryStats(
                        peaks_found=len(query_fingerprint['peaks']),
                        hashes_generated=len(query_fingerprint['hashes'])
                    ),
                    message="No matching song found"
                )
            
            best_match = matches[0]
            return IdentifyResponse(
                success=True,
                match_found=True,
                song=SongInfo(**best_match['song_info']),
                confidence=best_match['confidence'],
                match_details=MatchDetails(
                    coherent_matches=best_match['coherent_matches'],
                    total_matches=best_match['total_matches'],
                    song_offset=best_match['song_offset']
                ),
                query_stats=QueryStats(
                    peaks_found=len(query_fingerprint['peaks']),
                    hashes_generated=len(query_fingerprint['hashes'])
                ),
                all_matches=[
                    MatchInfo(
                        song_info=SongInfo(**m['song_info']),
                        confidence=m['confidence'],
                        coherent_matches=m['coherent_matches'],
                        total_matches=m['total_matches'],
                        song_offset=m['song_offset']
                    ) for m in matches
                ],
                message=f"Found matching song: {best_match['song_info']['title']} by {best_match['song_info']['artist']}"
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Error identifying song: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics"""
    try:
        with sqlite3.connect(fingerprinter.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM songs')
            total_songs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM fingerprints')
            total_fingerprints = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(fingerprint_count) FROM (SELECT COUNT(*) as fingerprint_count FROM fingerprints GROUP BY song_id)')
            avg_fingerprints_per_song = cursor.fetchone()[0] or 0.0
            
        return StatsResponse(
            database_stats=DatabaseStats(
                total_songs=total_songs,
                total_fingerprints=total_fingerprints,
                avg_fingerprints_per_song=avg_fingerprints_per_song
            )
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset", response_model=ResetResponse)
async def reset_database():
    """Reset the database (for development/testing purposes)"""
    try:
        with sqlite3.connect(fingerprinter.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS fingerprints')
            cursor.execute('DROP TABLE IF EXISTS songs')
            conn.commit()
        
        fingerprinter.init_database()
        return ResetResponse(success=True, message="Database reset successfully")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}", response_class=FileResponse)
async def get_file(filename: str):
    """Serve uploaded audio files"""
    file_path = os.path.join(os.getcwd(), filename)
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.warning(f"HTTP Exception: {exc.detail} (status code: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Generic exception handler"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "Internal server error"}
    )