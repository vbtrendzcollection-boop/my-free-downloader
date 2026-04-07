from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os

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
            # SUPER FALLBACK: Agar standard format na mile, toh jo bhi best/worst available ho usse select karo (taaki system crash na ho)
            'format': 'bestvideo+bestaudio/best/worstvideo+worstaudio/worst/all',
        }
        
        # SMART COOKIE FINDER: Checks all files in directory for the word 'cookie'
        cookie_files = [f for f in os.listdir('.') if 'cookie' in f.lower() and f.lower().endswith(('.txt', '.text'))]
        if cookie_files:
            ydl_opts['cookiefile'] = cookie_files[0]
            print(f"Using cookie file: {cookie_files[0]}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return {"status": "error", "message": "YouTube ne data nahi diya. Kripya video link check karein."}

            video_info = {
                "title": info.get('title', 'Video Title'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": []
            }

            # Step 1: Normal formats dhoondhna (Jisme Video aur Audio dono ho)
            for f in info.get('formats', []):
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                ext = f.get('ext', '')
                
                # Check for formats having both audio and video streams
                if f.get('url') and vcodec not in ['none', None] and acodec not in ['none', None]:
                    quality = f.get('format_note') or f.get('resolution') or 'Normal Quality'
                    video_info["formats"].append({
                        "quality": f"{quality} ({ext})",
                        "link": f.get('url')
                    })
            
            # Step 2: Agar combined formats bilkul na mile
            if len(video_info["formats"]) == 0:
                # Direct best available link fallback
                if info.get('url'):
                    video_info["formats"].append({
                        "quality": "Best Quality (Auto)",
                        "link": info.get('url')
                    })
                else:
                    # Backup: Grab whatever format has a valid URL
                    for f in info.get('formats', []):
                        if f.get('url') and f.get('vcodec') not in ['none', None]:
                            quality = f.get('format_note') or f.get('resolution') or 'Video'
                            video_info["formats"].append({
                                "quality": f"Basic Video ({f.get('ext', 'mp4')})",
                                "link": f.get('url')
                            })
                            break

            # Duplicates hatana taaki UI saaf dikhe
            unique_formats = []
            seen_links = set()
            for f in video_info["formats"]:
                if f["link"] not in seen_links:
                    unique_formats.append(f)
                    seen_links.add(f["link"])
            
            video_info["formats"] = unique_formats

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}
