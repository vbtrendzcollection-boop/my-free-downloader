from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# WordPress/Blogger frontend se connect hone ke liye zaroori hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Free Video Downloader API is running!"}

@app.get("/get-video")
def get_video(url: str):
    try:
        # Options me 'best' add kiya taki directly sabse best format mile
        ydl_opts = {
            'quiet': True, 
            'skip_download': True,
            'format': 'best'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            video_info = {
                "title": info.get('title', 'Video Title'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": []
            }

            # Sabse best combined format nikalna
            if info.get('url'):
                video_info["formats"].append({
                    "quality": info.get('format_note', 'Best Quality'),
                    "link": info.get('url')
                })
            
            # Baki formats ki list
            for f in info.get('formats', []):
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                    video_info["formats"].append({
                        "quality": f.get('format_note', 'MP4'),
                        "link": f.get('url')
                    })

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        # Pura error message capture karke wapas bhejna
        error_msg = str(e)
        return {"status": "error", "message": f"Server error detail: {error_msg}"}
