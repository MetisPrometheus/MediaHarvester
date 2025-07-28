import gradio as gr
import yt_dlp
import os
import tempfile

# Use an ephemeral, serverless‑safe tempdir
temp_dir = tempfile.gettempdir()

def download_video(url, platform):
    """Download video from the given platform into temp_dir."""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # optional cookies.txt if you commit it alongside this file
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        }
        if platform == "TikTok":
            ydl_opts['http_headers'] = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36'
                )
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fname = ydl.prepare_filename(info)
            base = fname.rsplit('.', 1)[0]
            for ext in ('.mp4', '.webm', '.mkv'):
                path = base + ext
                if os.path.exists(path):
                    return path, "✅ Downloaded successfully!"
            return None, "❌ File not found after download"

    except Exception as e:
        return None, f"❌ Error: {e}"

def download_youtube(url):
    if url.strip():
        return download_video(url, "YouTube")
    return None, "Please paste a YouTube Shorts URL"

def download_instagram(url):
    if url.strip():
        return download_video(url, "Instagram")
    return None, "Please paste an Instagram Reel URL"

def download_tiktok(url):
    if url.strip():
        return download_video(url, "TikTok")
    return None, "Please paste a TikTok URL"

def process_download(url, fn):
    """Wrapper to call the appropriate download function."""
    return fn(url)

# Custom CSS for the dark theme
custom_css = """
#app-container {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    min-height: 100vh;
}
.gradio-container {
    background: rgba(0, 0, 0, 0.8) !important;
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.gr-button {
    background: linear-gradient(45deg, #ff006e, #8338ec) !important;
    border: none !important;
    font-weight: bold !important;
    transition: all 0.3s ease !important;
}
.gr-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(131, 56, 236, 0.4);
}
.gr-input {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: white !important;
}
.gr-input::placeholder {
    color: rgba(255, 255, 255, 0.5) !important;
}
.gr-form {
    background: transparent !important;
}
h1, h2, h3 {
    color: white !important;
}
.platform-emoji {
    font-size: 2em;
    margin-right: 10px;
}
"""

with gr.Blocks(css=custom_css, title="Video Downloader", theme=gr.themes.Soft()) as demo:
    # Header
    gr.HTML("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #ff006e, #8338ec, #3cf0c5);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            ">
                ⚡ Quick Video Downloader
            </h1>
            <p style="color: rgba(255, 255, 255, 0.8);">
                Download videos from YouTube Shorts, Instagram Reels & TikTok
            </p>
        </div>
    """)

    # YouTube Shorts section
    with gr.Row():
        with gr.Column():
            gr.HTML('<h2><span class="platform-emoji">📺</span>YouTube Shorts</h2>')
            yt_input  = gr.Textbox(placeholder="Paste YouTube Shorts URL here…", label="", elem_id="yt-input")
            yt_button = gr.Button("Download YouTube Short", variant="primary", size="lg")
            yt_output = gr.File(label="Downloaded Video", visible=False)
            yt_status = gr.Textbox(label="Status", visible=False)

    # Instagram Reels section
    with gr.Row():
        with gr.Column():
            gr.HTML('<h2><span class="platform-emoji">📸</span>Instagram Reels</h2>')
            ig_input  = gr.Textbox(placeholder="Paste Instagram Reel URL here…", label="", elem_id="ig-input")
            ig_button = gr.Button("Download Instagram Reel", variant="primary", size="lg")
            ig_output = gr.File(label="Downloaded Video", visible=False)
            ig_status = gr.Textbox(label="Status", visible=False)

    # TikTok section
    with gr.Row():
        with gr.Column():
            gr.HTML('<h2><span class="platform-emoji">🎵</span>TikTok</h2>')
            tt_input  = gr.Textbox(placeholder="Paste TikTok URL here…", label="", elem_id="tt-input")
            tt_button = gr.Button("Download TikTok", variant="primary", size="lg")
            tt_output = gr.File(label="Downloaded Video", visible=False)
            tt_status = gr.Textbox(label="Status", visible=False)

    # Button callbacks
    yt_button.click(fn=lambda url: process_download(url, download_youtube),
                    inputs=[yt_input], outputs=[yt_output, yt_status])
    ig_button.click(fn=lambda url: process_download(url, download_instagram),
                    inputs=[ig_input], outputs=[ig_output, ig_status])
    tt_button.click(fn=lambda url: process_download(url, download_tiktok),
                    inputs=[tt_input], outputs=[tt_output, tt_status])

    # Footer tip
    gr.HTML("""
        <div style="text-align: center; margin-top: 40px; padding: 20px;
                    color: rgba(255, 255, 255, 0.6);">
            <p>💡 Tip: For Instagram, you might need to be logged in. Create a cookies.txt file if needed.</p>
        </div>
    """)

# **Do not launch locally**; instead expose the ASGI app:
app = demo.server_app
