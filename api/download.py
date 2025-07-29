from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
import tempfile
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response = json.dumps({
            "status": "ok",
            "message": "MemeYoink API is running! Use POST to download videos."
        })
        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        """Handle download requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON in request body")
                return
            
            url = data.get('url')
            platform = data.get('platform')
            
            if not url or not platform:
                self.send_error_response(400, "URL and platform are required")
                return
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                output_template = os.path.join(temp_dir, 'video.%(ext)s')
                
                # Configure yt-dlp options
                ydl_opts = {
                    'format': 'best[filesize<50M]/best',
                    'outtmpl': output_template,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                
                # Add platform-specific options
                if platform == 'tiktok':
                    ydl_opts['http_headers'] = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                
                # Download video
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=True)
                        
                        # Find downloaded file
                        downloaded_file = None
                        for file in os.listdir(temp_dir):
                            if file.startswith('video.'):
                                downloaded_file = os.path.join(temp_dir, file)
                                break
                        
                        if not downloaded_file or not os.path.exists(downloaded_file):
                            self.send_error_response(500, "Download completed but file not found")
                            return
                        
                        # Check file size
                        file_size = os.path.getsize(downloaded_file)
                        if file_size > 50 * 1024 * 1024:  # 50MB
                            self.send_error_response(413, "File too large (max 50MB)")
                            return
                        
                        # Read file content
                        with open(downloaded_file, 'rb') as f:
                            video_data = f.read()
                        
                        # Send video file response
                        self.send_response(200)
                        self.send_header('Content-Type', 'video/mp4')
                        self.send_header('Content-Length', str(len(video_data)))
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Disposition', 'attachment; filename=video.mp4')
                        self.end_headers()
                        self.wfile.write(video_data)
                        
                    except yt_dlp.utils.DownloadError as e:
                        error_msg = str(e)
                        if "Private video" in error_msg:
                            self.send_error_response(403, "This video is private")
                        elif "Video unavailable" in error_msg:
                            self.send_error_response(404, "Video not found or unavailable")
                        elif "Sign in" in error_msg:
                            self.send_error_response(403, "Age-restricted video")
                        else:
                            self.send_error_response(400, f"Download failed: {error_msg[:100]}")
                        
            finally:
                # Clean up temp directory
                if os.path.exists(temp_dir):
                    try:
                        for file in os.listdir(temp_dir):
                            os.unlink(os.path.join(temp_dir, file))
                        os.rmdir(temp_dir)
                    except:
                        pass
                        
        except Exception as e:
            self.send_error_response(500, f"Server error: {str(e)[:100]}")
    
    def send_error_response(self, code, message):
        """Send JSON error response"""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        error_response = json.dumps({"error": message})
        self.wfile.write(error_response.encode('utf-8'))