from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
import tempfile
import os
from urllib.parse import parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            url = data.get('url')
            platform = data.get('platform')
            
            if not url or not platform:
                self.send_error_response(400, "URL and platform are required")
                return
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[filesize<50M][ext=mp4]/best[filesize<50M]/best',
                'quiet': True,
                'no_warnings': True,
                'outtmpl': tempfile.mktemp(suffix='.mp4'),
            }
            
            # Add platform-specific options
            if platform == 'tiktok':
                ydl_opts['http_headers'] = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            
            # Download video to memory
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Find the downloaded file
                actual_filename = None
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_filename = filename.rsplit('.', 1)[0] + ext
                    if os.path.exists(test_filename):
                        actual_filename = test_filename
                        break
                
                if not actual_filename or not os.path.exists(actual_filename):
                    self.send_error_response(500, "Download failed")
                    return
                
                # Read file content
                with open(actual_filename, 'rb') as f:
                    video_data = f.read()
                
                # Clean up
                os.unlink(actual_filename)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(len(video_data)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(video_data)
                
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def send_error_response(self, code, message):
        error_response = json.dumps({'error': message})
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(error_response)))
        self.end_headers()
        self.wfile.write(error_response.encode('utf-8'))