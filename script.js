// DOM Elements
const form = document.getElementById('downloadForm');
const previewBtn = document.getElementById('previewBtn');
const downloadBtn = document.getElementById('downloadBtn');
const copyBtn = document.getElementById('copyBtn');
const previewSection = document.getElementById('previewSection');
const logSection = document.getElementById('logSection');
const commandPreview = document.getElementById('commandPreview');
const logOutput = document.getElementById('logOutput');

// Form inputs
const mpdUrlInput = document.getElementById('mpdUrl');
const licUrlInput = document.getElementById('licUrl');
const keyInput = document.getElementById('key');
const formatSelect = document.getElementById('format');
const outputDirInput = document.getElementById('outputDir');
const filenameInput = document.getElementById('filename');
const generateKeyBtn = document.getElementById('generateKeyBtn');

// State
let isDownloading = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Load saved values from localStorage
    loadSavedValues();
    
    // Add event listeners
    previewBtn.addEventListener('click', generateCommandPreview);
    copyBtn.addEventListener('click', copyCommand);
    form.addEventListener('submit', handleDownload);
    generateKeyBtn.addEventListener('click', generateKey);
    
    // Auto-save form values
    [mpdUrlInput, licUrlInput, keyInput, formatSelect, outputDirInput, filenameInput].forEach(input => {
        input.addEventListener('input', saveValues);
    });
});

// Generate key automatically
async function generateKey() {
    const mpdUrl = mpdUrlInput.value.trim();
    const licUrl = licUrlInput.value.trim();
    
    if (!mpdUrl || !licUrl) {
        showMessage('Bitte gib MPD URL und License URL ein!', 'error');
        return;
    }
    
    // Show loading state
    const originalText = generateKeyBtn.innerHTML;
    generateKeyBtn.disabled = true;
    generateKeyBtn.innerHTML = '<div class="loading"></div> Generating...';
    
    try {
        const response = await fetch('/api/generate-key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mpdUrl,
                licUrl
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            keyInput.value = result.key;
            showMessage('Key erfolgreich generiert!', 'success');
            saveValues(); // Save the generated key
        } else {
            showMessage(`Fehler beim Generieren des Keys: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Key generation error:', error);
        showMessage('Fehler beim Generieren des Keys!', 'error');
    } finally {
        // Restore button state
        generateKeyBtn.disabled = false;
        generateKeyBtn.innerHTML = originalText;
    }
}

// Generate command preview
function generateCommandPreview() {
    const mpdUrl = mpdUrlInput.value.trim();
    const key = keyInput.value.trim();
    const format = formatSelect.value;
    const outputDir = outputDirInput.value.trim();
    const filename = filenameInput.value.trim();
    
    if (!mpdUrl || !key) {
        showMessage('Bitte fülle alle Pflichtfelder aus!', 'error');
        return;
    }
    
    // Validate key format
    if (!isValidKeyFormat(key)) {
        showMessage('Ungültiges Key-Format! Erwartet: key:iv', 'error');
        return;
    }
    
    // Build command
    let command = './N_m3u8DL-RE';
    
    // Add format
    command += ` -M format=${format}`;
    
    // Add key
    command += ` --key ${key}`;
    
    // Add quality settings for best quality
    command += ` --select-video best --select-audio best`;
    
    // Add output directory if specified
    if (outputDir) {
        command += ` --save-dir "${outputDir}"`;
    }
    
    // Add filename if specified
    if (filename) {
        command += ` --save-name "${filename}"`;
    }
    
    // Add URL
    command += ` ${mpdUrl}`;
    
    // Display command
    commandPreview.textContent = command;
    previewSection.style.display = 'block';
    
    // Scroll to preview
    previewSection.scrollIntoView({ behavior: 'smooth' });
}

// Validate key format
function isValidKeyFormat(key) {
    // Check if key contains colon and has reasonable length
    const parts = key.split(':');
    return parts.length === 2 && parts[0].length >= 16 && parts[1].length >= 16;
}

// Copy command to clipboard
async function copyCommand() {
    try {
        await navigator.clipboard.writeText(commandPreview.textContent);
        showMessage('Befehl in Zwischenablage kopiert!', 'success');
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        copyBtn.style.background = '#28a745';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '#28a745';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy: ', err);
        showMessage('Fehler beim Kopieren!', 'error');
    }
}

// Handle download form submission
async function handleDownload(e) {
    e.preventDefault();
    
    if (isDownloading) {
        showMessage('Download läuft bereits!', 'error');
        return;
    }
    
    const mpdUrl = mpdUrlInput.value.trim();
    const key = keyInput.value.trim();
    const format = formatSelect.value;
    const outputDir = outputDirInput.value.trim();
    const filename = filenameInput.value.trim();
    
    if (!mpdUrl || !key) {
        showMessage('Bitte fülle alle Pflichtfelder aus!', 'error');
        return;
    }
    
    if (!isValidKeyFormat(key)) {
        showMessage('Ungültiges Key-Format! Erwartet: key:iv', 'error');
        return;
    }
    
    // Start download
    isDownloading = true;
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<div class="loading"></div> Downloading...';
    
    // Show log section
    logSection.style.display = 'block';
    logOutput.textContent = 'Starting download...\n';
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mpdUrl,
                key,
                format,
                outputDir: outputDir || './downloads',
                filename: filename || ''
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `HTTP error! status: ${response.status}`;
            throw new Error(errorMessage);
        }
        
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value);
            logOutput.textContent += chunk;
            logOutput.scrollTop = logOutput.scrollHeight;
        }
        
        showMessage('Download erfolgreich abgeschlossen!', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        logOutput.textContent += `\nError: ${error.message}\n`;
        showMessage('Download fehlgeschlagen!', 'error');
    } finally {
        isDownloading = false;
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Start Download';
    }
}

// Show message
function showMessage(message, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    // Insert at top of main content
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(messageDiv, mainContent.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Save form values to localStorage
function saveValues() {
    const values = {
        mpdUrl: mpdUrlInput.value,
        licUrl: licUrlInput.value,
        key: keyInput.value,
        format: formatSelect.value,
        outputDir: outputDirInput.value,
        filename: filenameInput.value
    };
    
    localStorage.setItem('mpd-dl-form', JSON.stringify(values));
}

// Load saved values from localStorage
function loadSavedValues() {
    try {
        const saved = localStorage.getItem('mpd-dl-form');
        if (saved) {
            const values = JSON.parse(saved);
            mpdUrlInput.value = values.mpdUrl || '';
            licUrlInput.value = values.licUrl || '';
            keyInput.value = values.key || '';
            formatSelect.value = values.format || 'mkv';
            outputDirInput.value = values.outputDir || '';
            filenameInput.value = values.filename || '';
        }
    } catch (error) {
        console.error('Error loading saved values:', error);
    }
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}
