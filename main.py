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
            # Yahan se saari format limitations hata di gayi hain
            # Ab ye bina kisi format error ke saara data le aayega
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
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                ext = f.get('ext', '')
                
                if f.get('url') and vcodec != 'none' and acodec != 'none':
                    quality = f.get('format_note') or f.get('resolution') or 'Normal Quality'
                    video_info["formats"].append({
                        "quality": f"{quality} ({ext})",
                        "link": f.get('url')
                    })
            
            # Step 2: Agar Normal formats na mile (Music videos ke case me)
            if len(video_info["formats"]) == 0:
                # Direct best available link use karein
                if info.get('url'):
                    video_info["formats"].append({
                        "quality": "Best Quality (Auto)",
                        "link": info.get('url')
                    })
                else:
                    # Backup: Koi bhi mp4 video format utha lo
                    for f in info.get('formats', []):
                        if f.get('ext') == 'mp4' and f.get('url'):
                            video_info["formats"].append({
                                "quality": "Basic MP4",
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
