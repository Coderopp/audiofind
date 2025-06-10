// Global variables
const API_BASE_URL = 'http://localhost:8000';
let currentTab = 'identify';

// DOM Elements
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const toastContainer = document.getElementById('toastContainer');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkServerHealth();
    loadStats();
    loadLibrary();
});

// Event Listeners
function initializeEventListeners() {
    // Tab navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Identify tab
    const identifyDropZone = document.getElementById('identifyDropZone');
    const identifyFileInput = document.getElementById('identifyFileInput');
    
    setupDropZone(identifyDropZone, identifyFileInput, handleIdentifyFile);

    // Fingerprint tab
    const fingerprintDropZone = document.getElementById('fingerprintDropZone');
    const fingerprintFileInput = document.getElementById('fingerprintFileInput');
    const fingerprintForm = document.getElementById('fingerprintForm');
    
    setupDropZone(fingerprintDropZone, fingerprintFileInput, handleFingerprintFile);
    fingerprintForm.addEventListener('submit', handleFingerprintSubmit);

    // Library tab
    document.getElementById('refreshLibrary').addEventListener('click', loadLibrary);
    document.getElementById('clearDatabase').addEventListener('click', clearDatabase);
    document.getElementById('librarySearch').addEventListener('input', handleLibrarySearch);
}

// Tab switching
function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
    });
    
    // Update tab content
    tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });

    // Load data if switching to library
    if (tabName === 'library') {
        loadLibrary();
    }
}

// Drop zone setup
function setupDropZone(dropZone, fileInput, handleFile) {
    // Click to browse
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// Handle identify file
async function handleIdentifyFile(file) {
    if (!isAudioFile(file)) {
        showToast('Please select a valid audio file', 'error');
        return;
    }

    const progressSection = document.getElementById('identifyProgress');
    const progressFill = document.getElementById('identifyProgressFill');
    const progressText = document.getElementById('identifyProgressText');
    const resultSection = document.getElementById('identifyResult');

    // Show progress
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    
    try {
        // Simulate progress
        animateProgress(progressFill, progressText, 'Analyzing audio...');

        const formData = new FormData();
        formData.append('audio', file);

        const response = await fetch(`${API_BASE_URL}/identify`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Complete progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Complete!';

        setTimeout(() => {
            progressSection.style.display = 'none';
            displayIdentifyResult(result);
        }, 500);

    } catch (error) {
        console.error('Error identifying song:', error);
        progressSection.style.display = 'none';
        showToast('Error identifying song: ' + error.message, 'error');
    }
}

// Handle fingerprint file selection
function handleFingerprintFile(file) {
    if (!isAudioFile(file)) {
        showToast('Please select a valid audio file', 'error');
        return;
    }

    // Update drop zone to show selected file
    const dropZone = document.getElementById('fingerprintDropZone');
    const content = dropZone.querySelector('.drop-zone-content');
    
    content.innerHTML = `
        <i class="fas fa-file-audio"></i>
        <h3>File Selected</h3>
        <p>${file.name}</p>
        <span class="file-types">Click to change file</span>
    `;
    
    // Store file for form submission
    dropZone.selectedFile = file;
}

// Handle fingerprint form submission
async function handleFingerprintSubmit(e) {
    e.preventDefault();
    
    const dropZone = document.getElementById('fingerprintDropZone');
    const file = dropZone.selectedFile;
    
    if (!file) {
        showToast('Please select an audio file', 'error');
        return;
    }

    const title = document.getElementById('songTitle').value.trim();
    const artist = document.getElementById('artistName').value.trim();

    if (!title || !artist) {
        showToast('Please fill in both title and artist', 'error');
        return;
    }

    const progressSection = document.getElementById('fingerprintProgress');
    const progressFill = document.getElementById('fingerprintProgressFill');
    const progressText = document.getElementById('fingerprintProgressText');
    const resultSection = document.getElementById('fingerprintResult');
    const submitButton = document.getElementById('fingerprintSubmit');

    // Show progress
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    submitButton.disabled = true;
    
    try {
        // Simulate progress
        animateProgress(progressFill, progressText, 'Creating fingerprint...');

        const formData = new FormData();
        formData.append('audio', file);
        formData.append('title', title);
        formData.append('artist', artist);

        const response = await fetch(`${API_BASE_URL}/fingerprint`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Complete progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Complete!';

        setTimeout(() => {
            progressSection.style.display = 'none';
            displayFingerprintResult(result);
            resetFingerprintForm();
            loadStats(); // Update stats
        }, 500);

        showToast('Song fingerprinted successfully!', 'success');

    } catch (error) {
        console.error('Error fingerprinting song:', error);
        progressSection.style.display = 'none';
        showToast('Error fingerprinting song: ' + error.message, 'error');
    } finally {
        submitButton.disabled = false;
    }
}

// Display identify result
function displayIdentifyResult(result) {
    const resultSection = document.getElementById('identifyResult');
    
    if (result.match_found) {
        const song = result.song;
        const confidence = result.confidence;
        const confidenceClass = getConfidenceClass(confidence);
        
        resultSection.innerHTML = `
            <div class="result-card">
                <div class="match-header">
                    <div class="match-info">
                        <h3>${song.title}</h3>
                        <p>by ${song.artist}</p>
                    </div>
                    <div class="confidence-badge ${confidenceClass}">
                        ${confidence}% match
                    </div>
                </div>
                <div class="match-details">
                    <p><strong>Duration:</strong> ${formatDuration(song.duration)}</p>
                    <p><strong>Matches found:</strong> ${result.match_details.coherent_matches} coherent matches</p>
                    <p><strong>Song offset:</strong> ${result.match_details.song_offset.toFixed(1)}s</p>
                </div>
            </div>
        `;
        
        if (result.all_matches.length > 1) {
            resultSection.innerHTML += '<h4>Other possible matches:</h4>';
            result.all_matches.slice(1, 4).forEach(match => {
                const matchConfidence = getConfidenceClass(match.confidence);
                resultSection.innerHTML += `
                    <div class="result-card">
                        <div class="match-header">
                            <div class="match-info">
                                <h3>${match.song_info.title}</h3>
                                <p>by ${match.song_info.artist}</p>
                            </div>
                            <div class="confidence-badge ${matchConfidence}">
                                ${match.confidence.toFixed(1)}% match
                            </div>
                        </div>
                    </div>
                `;
            });
        }
    } else {
        resultSection.innerHTML = `
            <div class="result-card">
                <div class="match-info">
                    <h3>No Match Found</h3>
                    <p>The song could not be identified in the database</p>
                </div>
                <div class="match-details">
                    <p><strong>Analysis:</strong> Found ${result.query_stats.peaks_found} peaks and generated ${result.query_stats.hashes_generated} hashes</p>
                    <p>Try adding this song to the database first, or ensure the audio quality is good.</p>
                </div>
            </div>
        `;
    }
    
    resultSection.style.display = 'block';
}

// Display fingerprint result
function displayFingerprintResult(result) {
    const resultSection = document.getElementById('fingerprintResult');
    
    resultSection.innerHTML = `
        <div class="result-card">
            <div class="match-info">
                <h3>Fingerprint Created Successfully!</h3>
                <p>${result.message}</p>
            </div>
            <div class="match-details">
                <p><strong>Song ID:</strong> ${result.song_id}</p>
                <p><strong>Duration:</strong> ${formatDuration(result.stats.duration)}</p>
                <p><strong>Peaks found:</strong> ${result.stats.peaks_found}</p>
                <p><strong>Fingerprints generated:</strong> ${result.stats.hashes_generated}</p>
            </div>
        </div>
    `;
    
    resultSection.style.display = 'block';
}

// Load library
async function loadLibrary() {
    try {
        const response = await fetch(`${API_BASE_URL}/songs`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayLibrary(data.songs);
        
    } catch (error) {
        console.error('Error loading library:', error);
        showToast('Error loading library: ' + error.message, 'error');
    }
}

// Display library
function displayLibrary(songs) {
    const libraryGrid = document.getElementById('libraryGrid');
    const emptyState = document.getElementById('emptyLibrary');
    
    if (songs.length === 0) {
        libraryGrid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    libraryGrid.style.display = 'grid';
    
    libraryGrid.innerHTML = songs.map(song => `
        <div class="song-card" onclick="showSongDetails(${song.id})">
            <h3>${song.title}</h3>
            <p class="artist">${song.artist}</p>
            <div class="song-meta">
                <span>Added: ${formatDate(song.created_at)}</span>
                <span class="duration">${formatDuration(song.duration)}</span>
            </div>
        </div>
    `).join('');
}

// Handle library search
function handleLibrarySearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    const songCards = document.querySelectorAll('.song-card');
    
    songCards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const artist = card.querySelector('.artist').textContent.toLowerCase();
        const matches = title.includes(searchTerm) || artist.includes(searchTerm);
        
        card.style.display = matches ? 'block' : 'none';
    });
}

// Clear database
async function clearDatabase() {
    if (!confirm('Are you sure you want to clear the entire database? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/reset`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        showToast('Database cleared successfully', 'success');
        loadLibrary();
        loadStats();
        
    } catch (error) {
        console.error('Error clearing database:', error);
        showToast('Error clearing database: ' + error.message, 'error');
    }
}

// Load stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const stats = data.database_stats;
        
        document.getElementById('songCount').textContent = stats.total_songs;
        document.getElementById('fingerprintCount').textContent = stats.total_fingerprints;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Check server health
async function checkServerHealth() {
    const healthIndicator = document.getElementById('healthIndicator');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        
        if (response.ok) {
            healthIndicator.classList.remove('offline');
        } else {
            healthIndicator.classList.add('offline');
        }
    } catch (error) {
        healthIndicator.classList.add('offline');
    }
}

// Utility functions
function isAudioFile(file) {
    const audioTypes = ['audio/mp3', 'audio/wav', 'audio/mpeg', 'audio/m4a', 'audio/flac'];
    return audioTypes.includes(file.type) || file.name.match(/\.(mp3|wav|m4a|flac)$/i);
}

function getConfidenceClass(confidence) {
    if (confidence >= 70) return 'confidence-high';
    if (confidence >= 40) return 'confidence-medium';
    return 'confidence-low';
}

function formatDuration(seconds) {
    if (!seconds) return 'Unknown';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function animateProgress(progressFill, progressText, text) {
    progressText.textContent = text;
    let progress = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) {
            progress = 90;
            clearInterval(interval);
        }
        progressFill.style.width = progress + '%';
    }, 200);
}

function resetFingerprintForm() {
    document.getElementById('fingerprintForm').reset();
    
    const dropZone = document.getElementById('fingerprintDropZone');
    const content = dropZone.querySelector('.drop-zone-content');
    
    content.innerHTML = `
        <i class="fas fa-cloud-upload-alt"></i>
        <h3>Drop your audio file here</h3>
        <p>or click to browse</p>
        <span class="file-types">Supports MP3, WAV, M4A, FLAC</span>
    `;
    
    delete dropZone.selectedFile;
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Modal functions
function showSongDetails(songId) {
    // This would fetch detailed song information
    // For now, we'll just show a simple implementation
    const modal = document.getElementById('songModal');
    const modalBody = document.getElementById('songModalBody');
    
    modalBody.innerHTML = `
        <p>Song ID: ${songId}</p>
        <p>Detailed information would be loaded here...</p>
    `;
    
    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('songModal').style.display = 'none';
}

// Close modal when clicking outside
document.getElementById('songModal').addEventListener('click', (e) => {
    if (e.target.id === 'songModal') {
        closeModal();
    }
});

// Make switchTab available globally
window.switchTab = switchTab;
window.showSongDetails = showSongDetails;
window.closeModal = closeModal;