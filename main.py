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
            # SUPER FALLBACK: Ye line wapas add ki gayi hai taaki format error kabhi na aaye
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

            audio_format = None
            video_formats = {}

            # Step 1: Saare formats ko filter karna
            for f in info.get('formats', []):
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                url_link = f.get('url')
                ext = f.get('ext')
                
                # Height ko safely number (integer) mein badalna
                try:
                    height = int(f.get('height', 0)) if f.get('height') else 0
                except:
                    height = 0

                if not url_link:
                    continue

                has_video = vcodec not in ['none', None]
                has_audio = acodec not in ['none', None]

                # Audio Only option dhoondhna
                if not has_video and has_audio:
                    if not audio_format or ext == 'm4a':
                        audio_format = {"quality": "Audio Only (MP3)", "link": url_link}

                # Video options (1080, 720, 480, 360) dhoondhna
                if has_video and height in [1080, 720, 480, 360]:
                    if height not in video_formats:
                        video_formats[height] = f
                    else:
                        current_has_audio = video_formats[height].get('acodec') not in ['none', None]
                        # Hamesha aawaz (audio) wale format ko priority do
                        if has_audio and not current_has_audio:
                            video_formats[height] = f
                        # Ya phir MP4 ko priority do
                        elif ext == 'mp4' and video_formats[height].get('ext') != 'mp4' and current_has_audio == has_audio:
                            video_formats[height] = f

            # Step 2: Formats ko list mein jodna (High to Low quality)
            for res in sorted(video_formats.keys(), reverse=True):
                f = video_formats[res]
                has_audio = f.get('acodec') not in ['none', None]
                
                # YouTube 1080p mein aawaz alag rakhta hai, isliye warning zaroori hai
                audio_tag = "" if has_audio else " (Mute/No Audio)"
                quality_name = f"{res}p HD" if res >= 720 else f"{res}p"
                
                video_info["formats"].append({
                    "quality": quality_name + audio_tag,
                    "link": f.get('url')
                })

            # Audio format ko sabse aakhir mein add karna
            if audio_format:
                video_info["formats"].append(audio_format)

            # Fallback agar kuch na mile
            if not video_info["formats"] and info.get('url'):
                video_info["formats"].append({
                    "quality": "Best Quality",
                    "link": info.get('url')
                })

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}
