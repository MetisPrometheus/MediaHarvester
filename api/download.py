import json
import yt_dlp
import tempfile
import os

def handler(request, response):
    """Vercel serverless function handler"""
    
    # Handle CORS
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    
    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        response.status_code = 200
        response.headers = headers
        return ""
    
    # Handle GET request - test endpoint
    if request.method == "GET":
        response.status_code = 200
        response.headers = {**headers, "Content-Type": "application/json"}
        return json.dumps({
            "status": "ok",
            "message": "MemeYoink API is running! Use POST to download videos."
        })
    
    # Only accept POST for downloads
    if request.method != "POST":
        response.status_code = 405
        response.headers = {**headers, "Content-Type": "application/json"}
        return json.dumps({"error": "Method not allowed. Use POST."})
    
    try:
        # Parse request body
        try:
            body = json.loads(request.body)
        except:
            response.status_code = 400
            response.headers = {**headers, "Content-Type": "application/json"}
            return json.dumps({"error": "Invalid JSON in request body"})
        
        url = body.get("url")
        platform = body.get("platform")
        
        if not url or not platform:
            response.status_code = 400
            response.headers = {**headers, "Content-Type": "application/json"}
            return json.dumps({"error": "URL and platform are required"})
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            output_template = os.path.join(temp_dir, "video.%(ext)s")
            
            # Configure yt-dlp
            ydl_opts = {
                "format": "best[filesize<50M]/best",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
            }
            
            # Add platform-specific options
            if platform == "tiktok":
                ydl_opts["http_headers"] = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    
                    # Find downloaded file
                    downloaded_file = None
                    for file in os.listdir(temp_dir):
                        if file.startswith("video."):
                            downloaded_file = os.path.join(temp_dir, file)
                            break
                    
                    if not downloaded_file:
                        response.status_code = 500
                        response.headers = {**headers, "Content-Type": "application/json"}
                        return json.dumps({"error": "Download completed but file not found"})
                    
                    # Check file size
                    file_size = os.path.getsize(downloaded_file)
                    if file_size > 50 * 1024 * 1024:  # 50MB
                        response.status_code = 413
                        response.headers = {**headers, "Content-Type": "application/json"}
                        return json.dumps({"error": "File too large (max 50MB)"})
                    
                    # Read file
                    with open(downloaded_file, "rb") as f:
                        video_data = f.read()
                    
                    # Return video file
                    response.status_code = 200
                    response.headers = {
                        **headers,
                        "Content-Type": "video/mp4",
                        "Content-Length": str(len(video_data)),
                        "Content-Disposition": "attachment; filename=video.mp4"
                    }
                    return video_data
                    
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e)
                    if "Private video" in error_msg:
                        message = "This video is private"
                    elif "Video unavailable" in error_msg:
                        message = "Video not found or unavailable"
                    elif "Sign in" in error_msg:
                        message = "Age-restricted video"
                    else:
                        message = f"Download failed: {error_msg[:100]}"
                    
                    response.status_code = 400
                    response.headers = {**headers, "Content-Type": "application/json"}
                    return json.dumps({"error": message})
                    
        finally:
            # Clean up
            try:
                for file in os.listdir(temp_dir):
                    os.unlink(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
            except:
                pass
                
    except Exception as e:
        response.status_code = 500
        response.headers = {**headers, "Content-Type": "application/json"}
        return json.dumps({"error": f"Server error: {str(e)[:100]}"})