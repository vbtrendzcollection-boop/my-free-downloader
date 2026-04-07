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
    # Tracking variable to see if cookies are found
    cookie_file_used = "Not Found"
    
    try:
        ydl_opts = {
            'quiet': True, 
            'skip_download': True,
            # 'format': 'best' yahan se hata diya gaya hai taaki format error na aaye
        }
        
        # SMART COOKIE FINDER: Checks all files in directory for the word 'cookie'
        cookie_files = [f for f in os.listdir('.') if 'cookie' in f.lower()]
        if cookie_files:
            ydl_opts['cookiefile'] = cookie_files[0]
            cookie_file_used = cookie_files[0]
            print(f"Using cookie file: {cookie_file_used}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            video_info = {
                "title": info.get('title', 'Video Title'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": []
            }

            # Saare formats check karna aur sirf wo nikalna jisme Video + Audio dono ho
            for f in info.get('formats', []):
                ext = f.get('ext', '')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                
                # Sirf direct chalne wale formats (acodec aur vcodec 'none' nahi hone chahiye)
                if f.get('url') and vcodec != 'none' and acodec != 'none':
                    quality = f.get('format_note') or f.get('resolution') or 'Video'
                    video_info["formats"].append({
                        "quality": f"{quality} ({ext})",
                        "link": f.get('url')
                    })
            
            # Agar koi specific combined format na mile, toh default video link bhej do
            if not video_info["formats"] and info.get('url'):
                video_info["formats"].append({
                    "quality": "Best Quality",
                    "link": info.get('url')
                })

            # Formats ko duplicate hone se bachana (optional clean-up)
            unique_formats = []
            seen_links = set()
            for f in video_info["formats"]:
                if f["link"] not in seen_links:
                    unique_formats.append(f)
                    seen_links.add(f["link"])
            
            video_info["formats"] = unique_formats

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        # Ab error message me ye bhi batayega ki konsi cookie file mili ya nahi mili
        error_msg = str(e)
        return {"status": "error", "message": f"Server error (Cookie File: {cookie_file_used}): {error_msg}"}
