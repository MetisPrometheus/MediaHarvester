import os, json, tempfile
from flask import Flask, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)

# CORS for every response
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/api/download", methods=["OPTIONS", "GET", "POST"])
def download():
    if request.method == "OPTIONS":
        return ("", 204)

    if request.method == "GET":
        return jsonify(status="ok", message="MemeYoink API is up!")

    data = request.get_json(silent=True) or {}
    url = data.get("url")
    platform = data.get("platform")
    if not url or not platform:
        return jsonify(error="URL and platform are required"), 400

    # temp dir in Lambda-like env
    tmp = tempfile.mkdtemp()
    outtpl = os.path.join(tmp, "video.%(ext)s")

    ydl_opts = {
      "format": "best[filesize<50M]/best",
      "outtmpl": outtpl,
      "quiet": True,
      "no_warnings": True,
    }
    # TikTok UA bypass
    if platform == "tiktok":
      ydl_opts["http_headers"] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      }

    try:
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
      # Find the downloaded file
      files = os.listdir(tmp)
      vid = next(f for f in files if f.startswith("video."))
      path = os.path.join(tmp, vid)

      # Flask will stream this file back
      return send_file(
        path,
        mimetype="video/mp4",
        as_attachment=True,
        download_name="video.mp4"
      )
    except yt_dlp.utils.DownloadError as e:
      msg = str(e)
      code = 400
      if "Private video" in msg:    code=403; msg="This video is private"
      if "Video unavailable" in msg:code=404; msg="Video not found"
      return jsonify(error=msg), code
    finally:
      # cleanup
      for f in os.listdir(tmp):
        try: os.unlink(os.path.join(tmp, f))
        except: pass
      try: os.rmdir(tmp)
      except: pass

# Vercel’s Python runtime will detect the `app` WSGI object
