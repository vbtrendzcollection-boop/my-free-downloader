from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import glob

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
        ydl_opts = {
            'quiet': True, 
            'skip_download': True,
            'format': 'best',
            # YOUTUBE BYPASS: Sirf Mobile clients ka use karenge, 'web' ko hata diya taaki bot error na aaye
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios']
                }
            }
        }
        
        # SMART COOKIE FINDER: Ye automatically kisi bhi cookie file (jaise youtube.com cookies.text) ko dhoondh lega
        cookie_files = [f for f in os.listdir('.') if 'cookie' in f.lower() and f.lower().endswith(('.txt', '.text'))]
        if cookie_files:
            ydl_opts['cookiefile'] = cookie_files[0]
            print(f"Using cookie file: {cookie_files[0]}")
        
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
