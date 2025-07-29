import json
import yt_dlp
import tempfile
import os
from urllib.parse import parse_qs

def handler(request, response):
    """Vercel serverless function handler"""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response.status_code = 200
        response.headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
        return response
    
    # Only accept POST requests
    if request.method != "POST":
        response.status_code = 405
        response.headers = {"Access-Control-Allow-Origin": "*"}
        return json.dumps({"error": "Method not allowed"})
    
    try:
        # Parse request body
        body = json.loads(request.body)
        url = body.get("url")
        platform = body.get("platform")
        
        if not url or not platform:
            response.status_code = 400
            response.headers = {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
            return json.dumps({"error": "URL and platform are required"})
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "video.mp4")
        
        # Configure yt-dlp options
        ydl_opts = {
            "format": "best[filesize<50M][ext=mp4]/best[filesize<50M]/best",
            "quiet": True,
            "no_warnings": True,
            "outtmpl": output_path,
            "max_filesize": 50 * 1024 * 1024,  # 50MB limit
        }
        
        # Add platform-specific options
        if platform == "tiktok":
            ydl_opts["http_headers"] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            actual_file = None
            for ext in [".mp4", ".webm", ".mkv", ".mov"]:
                test_path = output_path.replace(".mp4", ext)
                if os.path.exists(test_path):
                    actual_file = test_path
                    break
            
            if not actual_file:
                # Check if file exists without extension change
                if os.path.exists(output_path):
                    actual_file = output_path
                else:
                    raise Exception("Download failed - file not found")
            
            # Read file content
            with open(actual_file, "rb") as f:
                video_data = f.read()
            
            # Clean up
            try:
                os.unlink(actual_file)
                os.rmdir(temp_dir)
            except:
                pass
            
            # Return video file
            response.status_code = 200
            response.headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(video_data)),
                "Access-Control-Allow-Origin": "*",
                "Content-Disposition": "attachment; filename=video.mp4"
            }
            return video_data
            
    except Exception as e:
        # Clean up on error
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    os.unlink(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
        except:
            pass
        
        response.status_code = 500
        response.headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
        return json.dumps({"error": str(e)})