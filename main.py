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
            # 'all' formats nikalenge taaki hum manual 1080p, 720p filter kar sakein
            'format': 'all',
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

            desired_resolutions = [1080, 720, 480, 360]
            found_formats = {}

            # Step 1: Saare formats check karke 1080p, 720p, 480p, 360p nikalna
            for f in info.get('formats', []):
                height = f.get('height')
                url_link = f.get('url')
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                ext = f.get('ext')

                # Video streams hi check karenge is loop me
                if not url_link or vcodec in ['none', None]:
                    continue

                if height in desired_resolutions:
                    has_audio = acodec not in ['none', None]
                    
                    # Store the format. Prefer formats with audio or MP4 extension
                    if height not in found_formats:
                        found_formats[height] = f
                    else:
                        current_has_audio = found_formats[height].get('acodec') not in ['none', None]
                        # Agar naye wale me audio hai aur purane me nahi, toh replace kar do
                        if has_audio and not current_has_audio:
                            found_formats[height] = f
                        # Ya phir MP4 format ko priority do
                        elif ext == 'mp4' and found_formats[height].get('ext') != 'mp4' and current_has_audio == has_audio:
                            found_formats[height] = f

            # Quality Options ko sort karna (1080p se 360p tak)
            for res in sorted(found_formats.keys(), reverse=True):
                f = found_formats[res]
                has_audio = f.get('acodec') not in ['none', None]
                
                # YouTube 1080p me video aur audio alag deta hai, toh user ko batana zaroori hai
                audio_warning = "" if has_audio else " (No Audio)"
                quality_label = f"{res}p HD" if res >= 720 else f"{res}p"
                
                video_info["formats"].append({
                    "quality": quality_label + audio_warning,
                    "link": f.get('url')
                })

            # Step 2: Ek Audio Only (MP3/M4A) ka option add karna
            for f in info.get('formats', []):
                if f.get('vcodec') in ['none', None] and f.get('acodec') not in ['none', None]:
                    video_info["formats"].append({
                        "quality": "Audio Only (MP3)",
                        "link": f.get('url')
                    })
                    break # Ek audio link kaafi hai
            
            # Step 3: Agar by chance koi format match na ho, toh best link de do
            if len(video_info["formats"]) == 0 and info.get('url'):
                video_info["formats"].append({
                    "quality": "Best Available Quality",
                    "link": info.get('url')
                })

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}
