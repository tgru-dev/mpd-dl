#!/usr/bin/env python3
"""
N_m3u8DL-RE Web UI Backend
Flask server for handling N_m3u8DL-RE binary execution
"""

import os
import sys
import json
import subprocess
import threading
import time
import requests
import base64
import re
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import logging
from lxml import etree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
BINARY_PATH = './N_m3u8DL-RE'
DEFAULT_OUTPUT_DIR = './downloads'
ALLOWED_FORMATS = ['mkv', 'mp4', 'ts', 'm4s']

# Ensure output directory exists
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

class DownloadManager:
    def __init__(self):
        self.active_downloads = {}
        self.download_counter = 0
    
    def start_download(self, download_id, mpd_url, key, format_type, output_dir, filename=None):
        """Start a new download process"""
        try:
            # Build command
            cmd = [BINARY_PATH, '-M', f'format={format_type}', '--key', key]
            
            # Add quality settings for best quality
            cmd.extend(['--select-video', 'best', '--select-audio', 'best'])
            
            if output_dir:
                cmd.extend(['--save-dir', output_dir])
            
            if filename:
                cmd.extend(['--save-name', filename])
            
            cmd.append(mpd_url)
            
            logger.info(f"Starting download {download_id}: {' '.join(cmd)}")
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.active_downloads[download_id] = {
                'process': process,
                'start_time': time.time(),
                'status': 'running'
            }
            
            logger.info(f"Process started with PID: {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"Error starting download {download_id}: {e}")
            raise
    
    def get_download_status(self, download_id):
        """Get status of a download"""
        if download_id not in self.active_downloads:
            return None
        
        download = self.active_downloads[download_id]
        process = download['process']
        
        if process.poll() is not None:
            # Process finished
            download['status'] = 'completed' if process.returncode == 0 else 'failed'
            download['end_time'] = time.time()
            download['return_code'] = process.returncode
        
        return download
    
    def stop_download(self, download_id):
        """Stop a running download"""
        if download_id in self.active_downloads:
            download = self.active_downloads[download_id]
            process = download['process']
            
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            download['status'] = 'stopped'
            download['end_time'] = time.time()

# Global download manager
download_manager = DownloadManager()

class KeyGenerator:
    def __init__(self):
        self.api_url = 'https://cdrm-project.com/api/decrypt'
    
    def extract_pssh_from_mpd(self, mpd_url):
        """Extract PSSH from MPD file"""
        try:
            logger.info(f"Fetching MPD from: {mpd_url}")
            response = requests.get(mpd_url, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = etree.fromstring(response.content)
            
            # Find PSSH in ContentProtection elements
            pssh_values = []
            for protection in root.xpath('//ContentProtection'):
                scheme_id_uri = protection.get('schemeIdUri', '')
                if 'pssh' in scheme_id_uri.lower() or 'widevine' in scheme_id_uri.lower():
                    # Look for PSSH in child elements
                    for child in protection:
                        if child.tag.endswith('PSSH') or child.text:
                            pssh_text = child.text
                            if pssh_text and pssh_text.strip():
                                pssh_values.append(pssh_text.strip())
            
            # Also search for base64 encoded PSSH in the XML content
            xml_content = response.text
            pssh_pattern = r'<[^>]*PSSH[^>]*>([A-Za-z0-9+/=]+)</[^>]*PSSH[^>]*>'
            matches = re.findall(pssh_pattern, xml_content, re.IGNORECASE)
            pssh_values.extend(matches)
            
            # Search for any base64 strings that look like PSSH
            base64_pattern = r'[A-Za-z0-9+/]{100,}={0,2}'
            all_base64 = re.findall(base64_pattern, xml_content)
            for b64 in all_base64:
                try:
                    decoded = base64.b64decode(b64)
                    if b'pssh' in decoded.lower() or b'widevine' in decoded.lower():
                        pssh_values.append(b64)
                except:
                    continue
            
            if pssh_values:
                # Return the first valid PSSH
                logger.info(f"Found {len(pssh_values)} PSSH values")
                return pssh_values[0]
            else:
                logger.warning("No PSSH found in MPD")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting PSSH: {e}")
            return None
    
    def generate_key(self, pssh, lic_url):
        """Generate decryption key using the API"""
        try:
            logger.info(f"Generating key for PSSH: {pssh[:50]}...")
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                'pssh': pssh,
                'licurl': lic_url,
                'headers': str({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                })
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            message = result.get('message', '')
            
            if message:
                # Extract keys from the message (usually contains multiple keys)
                # Look for key:iv pattern
                key_pattern = r'([a-f0-9]{32}):([a-f0-9]{32})'
                matches = re.findall(key_pattern, message, re.IGNORECASE)
                
                if matches:
                    # Return the first key:iv pair
                    key, iv = matches[0]
                    logger.info(f"Generated key: {key}:{iv}")
                    return f"{key}:{iv}"
                else:
                    logger.error(f"No valid key found in response: {message}")
                    return None
            else:
                logger.error(f"Empty response from API: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating key: {e}")
            return None

# Global key generator
key_generator = KeyGenerator()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

@app.route('/api/generate-key', methods=['POST'])
def generate_key():
    """Generate decryption key automatically"""
    try:
        data = request.get_json()
        
        mpd_url = data.get('mpdUrl', '').strip()
        lic_url = data.get('licUrl', '').strip()
        
        if not mpd_url:
            return jsonify({'error': 'MPD URL is required'}), 400
        
        if not lic_url:
            return jsonify({'error': 'License URL is required'}), 400
        
        # Extract PSSH from MPD
        pssh = key_generator.extract_pssh_from_mpd(mpd_url)
        if not pssh:
            return jsonify({'error': 'Could not extract PSSH from MPD file'}), 400
        
        # Generate key using API
        key = key_generator.generate_key(pssh, lic_url)
        if not key:
            return jsonify({'error': 'Could not generate decryption key'}), 400
        
        return jsonify({
            'success': True,
            'key': key,
            'pssh': pssh
        })
        
    except Exception as e:
        logger.error(f"Error in generate_key: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    """Start a new download"""
    try:
        data = request.get_json()
        
        # Validate input
        mpd_url = data.get('mpdUrl', '').strip()
        key = data.get('key', '').strip()
        format_type = data.get('format', 'mkv')
        output_dir = data.get('outputDir', DEFAULT_OUTPUT_DIR).strip()
        filename = data.get('filename', '') or ''
        filename = filename.strip() if filename else None
        
        if not mpd_url or not key:
            return jsonify({'error': 'MPD URL and key are required'}), 400
        
        if format_type not in ALLOWED_FORMATS:
            return jsonify({'error': f'Invalid format. Allowed: {", ".join(ALLOWED_FORMATS)}'}), 400
        
        # Validate key format
        if ':' not in key or len(key.split(':')) != 2:
            return jsonify({'error': 'Invalid key format. Expected: key:iv'}), 400
        
        # Generate download ID
        download_id = f"download_{int(time.time())}"
        
        # Ensure output directory exists
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        # Start download
        process = download_manager.start_download(
            download_id, mpd_url, key, format_type, output_dir, filename
        )
        
        def generate():
            """Generator for streaming output"""
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        yield line
                
                # Wait for process to complete
                process.wait()
                
                if process.returncode == 0:
                    yield f"\n✅ Download completed successfully!\n"
                else:
                    yield f"\n❌ Download failed with return code {process.returncode}\n"
                    
            except Exception as e:
                yield f"\n❌ Error during download: {str(e)}\n"
            finally:
                # Clean up
                if download_id in download_manager.active_downloads:
                    del download_manager.active_downloads[download_id]
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Error in start_download: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<download_id>')
def get_download_status(download_id):
    """Get status of a specific download"""
    status = download_manager.get_download_status(download_id)
    if status is None:
        return jsonify({'error': 'Download not found'}), 404
    
    return jsonify(status)

@app.route('/api/downloads')
def list_downloads():
    """List all active downloads"""
    downloads = {}
    for download_id, download in download_manager.active_downloads.items():
        downloads[download_id] = {
            'status': download['status'],
            'start_time': download['start_time'],
            'duration': time.time() - download['start_time']
        }
    
    return jsonify(downloads)

@app.route('/api/stop/<download_id>', methods=['POST'])
def stop_download(download_id):
    """Stop a running download"""
    try:
        download_manager.stop_download(download_id)
        return jsonify({'message': 'Download stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_input():
    """Validate input without starting download"""
    try:
        data = request.get_json()
        
        mpd_url = data.get('mpdUrl', '').strip()
        key = data.get('key', '').strip()
        format_type = data.get('format', 'mkv')
        
        errors = []
        
        if not mpd_url:
            errors.append('MPD URL is required')
        elif not (mpd_url.startswith('http://') or mpd_url.startswith('https://')):
            errors.append('MPD URL must start with http:// or https://')
        
        if not key:
            errors.append('Key is required')
        elif ':' not in key or len(key.split(':')) != 2:
            errors.append('Invalid key format. Expected: key:iv')
        
        if format_type not in ALLOWED_FORMATS:
            errors.append(f'Invalid format. Allowed: {", ".join(ALLOWED_FORMATS)}')
        
        # Check if binary exists
        if not os.path.exists(BINARY_PATH):
            errors.append(f'N_m3u8DL-RE binary not found at {BINARY_PATH}')
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'binary_exists': os.path.exists(BINARY_PATH),
        'active_downloads': len(download_manager.active_downloads)
    })

if __name__ == '__main__':
    # Check if binary exists
    if not os.path.exists(BINARY_PATH):
        logger.error(f"N_m3u8DL-RE binary not found at {BINARY_PATH}")
        logger.error("Please ensure the binary is in the same directory as this script")
        sys.exit(1)
    
    # Make binary executable
    os.chmod(BINARY_PATH, 0o755)
    
    logger.info("Starting N_m3u8DL-RE Web UI server...")
    logger.info(f"Binary path: {BINARY_PATH}")
    logger.info(f"Default output directory: {DEFAULT_OUTPUT_DIR}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=7421,
        debug=True,
        threaded=True
    )
