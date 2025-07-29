import { useState } from "react";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [platform, setPlatform] = useState("youtube");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const download = async () => {
    if (!url.trim()) {
      setError("Please enter a URL");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      const response = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, platform }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Download failed");
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `video_${Date.now()}.mp4`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setUrl("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="content">
        <h1>⚡Quick Meme Yoinker</h1>
        <p className="subtitle">
          Download videos from YouTube Shorts, Instagram Reels & TikTok
        </p>

        <div className="form-group">
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="platform-select"
          >
            <option value="youtube">📺 YouTube Shorts</option>
            <option value="instagram">📸 Instagram Reels</option>
            <option value="tiktok">🎵 TikTok</option>
          </select>

          <input
            type="text"
            placeholder="Paste video URL here..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && download()}
            className="url-input"
          />

          <button
            onClick={download}
            disabled={loading}
            className="download-btn"
          >
            {loading ? "Downloading..." : "Download"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && (
          <div className="success">✅ Meme successfully yoinked!</div>
        )}

        <div className="tips">
          <p>💡 Tips:</p>
          <ul>
            <li>Make sure the URL is publicly accessible</li>
            <li>Instagram may require authentication for some videos</li>
            <li>Downloads may take a few seconds</li>
            <li>Max file size: 50MB</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
