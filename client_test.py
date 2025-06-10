# Client Test Script for Audio Fingerprinting Backend
# Requirements: pip install requests

import requests
import json
import os
from pathlib import Path

class AudioFingerprintClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
    
    def health_check(self):
        """Check if backend is running"""
        try:
            response = requests.get(f'{self.base_url}/health')
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def get_songs(self):
        """Get all songs in database"""
        response = requests.get(f'{self.base_url}/songs')
        return response.json()
    
    def fingerprint_song(self, audio_path, title=None, artist=None):
        """Add song to database"""
        if not os.path.exists(audio_path):
            return {'error': f'File not found: {audio_path}'}
        
        # Extract title from filename if not provided
        if not title:
            title = Path(audio_path).stem
        
        if not artist:
            artist = 'Unknown Artist'
        
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'title': title, 'artist': artist}
            
            response = requests.post(f'{self.base_url}/fingerprint', files=files, data=data)
            return response.json()
    
    def identify_song(self, audio_path):
        """Identify song from audio snippet"""
        if not os.path.exists(audio_path):
            return {'error': f'File not found: {audio_path}'}
        
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            response = requests.post(f'{self.base_url}/identify', files=files)
            return response.json()
    
    def get_stats(self):
        """Get database statistics"""
        response = requests.get(f'{self.base_url}/stats')
        return response.json()
    
    def reset_database(self):
        """Reset database"""
        response = requests.post(f'{self.base_url}/reset')
        return response.json()

def test_client():
    """Test the audio fingerprinting system"""
    client = AudioFingerprintClient()
    
    print("🔍 Testing Audio Fingerprinting Backend")
    print("=" * 50)
    
    # Health check
    print("1. Health Check...")
    health = client.health_check()
    if health:
        print(f"   ✅ Backend is running: {health['status']}")
    else:
        print("   ❌ Backend is not accessible")
        return
    
    # Get initial stats
    print("\n2. Initial Database Stats...")
    stats = client.get_stats()
    print(f"   📊 Songs: {stats['database_stats']['total_songs']}")
    print(f"   📊 Fingerprints: {stats['database_stats']['total_fingerprints']}")
    
    # Example usage - you'll need to provide actual audio files
    audio_dir = "./audio_samples"  # Change this to your audio directory
    
    if os.path.exists(audio_dir):
        print(f"\n3. Testing with audio files from {audio_dir}...")
        
        # Find audio files
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.m4a', '*.flac']:
            audio_files.extend(Path(audio_dir).glob(ext))
        
        audio_files = audio_files[:3]  # Limit to 3 files for testing
        
        if audio_files:
            # Add songs to database
            print("   📝 Adding songs to database...")
            for audio_file in audio_files:
                print(f"      Processing: {audio_file.name}")
                result = client.fingerprint_song(str(audio_file))
                if result.get('success'):
                    print(f"      ✅ Added: {result['stats']['hashes_generated']} hashes")
                else:
                    print(f"      ❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Test identification with first file
            if audio_files:
                print(f"\n   🔍 Testing identification with {audio_files[0].name}...")
                result = client.identify_song(str(audio_files[0]))
                if result.get('success') and result.get('match_found'):
                    match = result['song']
                    print(f"      ✅ Identified: {match['title']} by {match['artist']}")
                    print(f"      📊 Confidence: {result['confidence']}%")
                else:
                    print(f"      ❌ No match found or error occurred")
        else:
            print(f"   ⚠️  No audio files found in {audio_dir}")
    else:
        print(f"\n3. ⚠️  Audio directory {audio_dir} not found")
        print("   Create the directory and add some audio files to test fingerprinting")
    
    # Final stats
    print("\n4. Final Database Stats...")
    stats = client.get_stats()
    print(f"   📊 Songs: {stats['database_stats']['total_songs']}")
    print(f"   📊 Fingerprints: {stats['database_stats']['total_fingerprints']}")
    print(f"   📊 Avg fingerprints per song: {stats['database_stats']['avg_fingerprints_per_song']}")
    
    # List all songs
    print("\n5. Songs in Database...")
    songs = client.get_songs()
    if songs['songs']:
        for song in songs['songs']:
            print(f"   🎵 {song['title']} by {song['artist']} ({song['filename']})")
    else:
        print("   📭 No songs in database")
    
    print("\n✅ Test completed!")

def interactive_mode():
    """Interactive mode for testing"""
    client = AudioFingerprintClient()
    
    print("🎵 Audio Fingerprinting Interactive Client")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Add song to database")
        print("2. Identify song")
        print("3. List all songs")
        print("4. Database stats")
        print("5. Reset database")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            audio_path = input("Audio file path: ").strip()
            title = input("Song title (optional): ").strip() or None
            artist = input("Artist name (optional): ").strip() or None
            
            result = client.fingerprint_song(audio_path, title, artist)
            if result.get('success'):
                print(f"✅ Song added successfully!")
                print(f"   Peaks: {result['stats']['peaks_found']}")
                print(f"   Hashes: {result['stats']['hashes_generated']}")
            else:
                print(f"❌ Error: {result.get('error')}")
        
        elif choice == '2':
            audio_path = input("Audio snippet path: ").strip()
            
            result = client.identify_song(audio_path)
            if result.get('success') and result.get('match_found'):
                match = result['song']
                print(f"🎵 Match found: {match['title']} by {match['artist']}")
                print(f"📊 Confidence: {result['confidence']}%")
                print(f"🔍 Matches: {result['match_details']['coherent_matches']}/{result['match_details']['total_matches']}")
            elif result.get('success'):
                print("❌ No match found")
            else:
                print(f"❌ Error: {result.get('error')}")
        
        elif choice == '3':
            songs = client.get_songs()
            print(f"\n📚 {songs['count']} songs in database:")
            for song in songs['songs']:
                print(f"   🎵 {song['title']} by {song['artist']}")
        
        elif choice == '4':
            stats = client.get_stats()
            db_stats = stats['database_stats']
            print(f"\n📊 Database Statistics:")
            print(f"   Songs: {db_stats['total_songs']}")
            print(f"   Fingerprints: {db_stats['total_fingerprints']}")
            print(f"   Avg per song: {db_stats['avg_fingerprints_per_song']}")
        
        elif choice == '5':
            confirm = input("Are you sure you want to reset the database? (yes/NO): ")
            if confirm.lower() == 'yes':
                result = client.reset_database()
                if result.get('success'):
                    print("✅ Database reset successfully")
                else:
                    print(f"❌ Error: {result.get('error')}")
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == '__main__':
    print("Audio Fingerprinting Client")
    print("Choose mode:")
    print("1. Run automated test")
    print("2. Interactive mode")
    
    mode = input("Enter choice (1-2): ").strip()
    
    if mode == '1':
        test_client()
    elif mode == '2':
        interactive_mode()
    else:
        print("Invalid choice")