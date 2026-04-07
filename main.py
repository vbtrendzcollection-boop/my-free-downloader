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
            'format': 'bestvideo+bestaudio/best/all', # Sab kuch nikalo taaki hum filter kar sakein
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

            # Step 1: Saare formats ko STRICTLY filter karna
            for f in info.get('formats', []):
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                url_link = f.get('url')
                ext = f.get('ext')
                protocol = f.get('protocol', '')
                format_id = f.get('format_id', '')
                
                # Height ko safely number (integer) mein badalna
                try:
                    height = int(f.get('height', 0)) if f.get('height') else 0
                except:
                    height = 0

                # 🚨 STRICT FILTER: Images, storyboards (sb), dash, aur m3u8 files ko reject karo
                if not url_link or not url_link.startswith('http'):
                    continue
                if 'sb' in format_id or ext in ['mhtml', 'webp', 'jpg', 'png', 'gif']:
                    continue
                if 'm3u8' in protocol or 'dash' in protocol:
                    continue

                has_video = vcodec not in ['none', None]
                has_audio = acodec not in ['none', None]

                # Audio Only option dhoondhna
                if not has_video and has_audio:
                    if not audio_format or ext == 'm4a':
                        audio_format = {"quality": "Audio Only (MP3)", "link": url_link}

                # Video options dhoondhna (Sirf valid video formats like MP4/WebM)
                if has_video and height > 0 and ext in ['mp4', 'webm']:
                    # Agar height exactly 1080 na ho kar 1078 bhi ho, toh use store kar lenge
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

            # Step 2: Formats ko list mein jodna (High to Low quality sorting)
            for res in sorted(video_formats.keys(), reverse=True):
                f = video_formats[res]
                has_audio = f.get('acodec') not in ['none', None]
                
                # YouTube high quality (1080p+) mein aawaz alag rakhta hai
                audio_tag = "" if has_audio else " (Mute/No Audio)"
                
                # Dynamic naming (1080p, 720p, etc. bajaye exact height ke)
                if res >= 1080: quality_name = "1080p HD"
                elif res >= 720: quality_name = "720p HD"
                elif res >= 480: quality_name = "480p"
                elif res >= 360: quality_name = "360p"
                else: quality_name = f"{res}p"
                
                video_info["formats"].append({
                    "quality": quality_name + audio_tag,
                    "link": f.get('url')
                })

            # Duplicate qualities ko ek saath merge kar dena taki 1080p do baar na dikhe
            unique_formats = []
            seen_qualities = set()
            for format_obj in video_info["formats"]:
                if format_obj["quality"] not in seen_qualities:
                    unique_formats.append(format_obj)
                    seen_qualities.add(format_obj["quality"])
            
            video_info["formats"] = unique_formats

            # Audio format ko sabse aakhir mein add karna
            if audio_format:
                video_info["formats"].append(audio_format)

            # Fallback agar Filter hone ke baad list khali ho jaye
            if not video_info["formats"]:
                # Default jo sabse best original video link ho, wo de do
                if info.get('url'):
                    video_info["formats"].append({
                        "quality": "Best Quality Video",
                        "link": info.get('url')
                    })
                else:
                    # Akhiri koshish, koi bhi valid video nikal lo
                    for f in info.get('formats', []):
                        if f.get('url') and f.get('vcodec') not in ['none', None] and f.get('ext') == 'mp4' and f.get('url').startswith('http'):
                            video_info["formats"].append({"quality": "Best Available MP4", "link": f.get('url')})
                            break

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}
