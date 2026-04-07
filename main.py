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
            # ERROR FIX: 'ignore_no_formats_error' ko True kar diya hai.
            # Ab koi format available na hone par bhi yt-dlp crash nahi hoga, balki raw formats de dega.
            'ignore_no_formats_error': True,
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
                url_link = f.get('url', '')
                ext = f.get('ext', '')
                protocol = f.get('protocol', '')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                
                # Sabse zaroori: "format_note" aur "format_id" check karna
                format_note = str(f.get('format_note', '')).lower()
                format_id = str(f.get('format_id', '')).lower()
                
                # 🚨 100% BULLETPROOF FILTER 🚨
                # Storyboards (chhoti images) aur invalid formats ko completely block karein
                if 'storyboard' in format_note or 'sb' in format_id:
                    continue
                if ext in ['mhtml', 'webp', 'jpg', 'png', 'gif']:
                    continue
                if not url_link or not url_link.startswith('http'):
                    continue
                if 'm3u8' in protocol or 'dash' in protocol:
                    continue

                has_video = vcodec not in ['none', None]
                has_audio = acodec not in ['none', None]

                try:
                    height = int(f.get('height', 0)) if f.get('height') else 0
                except:
                    height = 0

                # Audio Only option dhoondhna
                if not has_video and has_audio:
                    if not audio_format or ext in ['m4a', 'mp3']:
                        audio_format = {"quality": "Audio Only (MP3/M4A)", "link": url_link}

                # Video options (Strictly heights with video and MP4/WebM)
                if has_video and height > 0 and ext in ['mp4', 'webm']:
                    if height not in video_formats:
                        video_formats[height] = f
                    else:
                        current_f = video_formats[height]
                        current_has_audio = current_f.get('acodec') not in ['none', None]
                        
                        # Priority 1: Hamesha aawaz (audio) wale format ko priority do
                        if has_audio and not current_has_audio:
                            video_formats[height] = f
                        # Priority 2: Agar dono me audio hai, toh MP4 ko priority do
                        elif has_audio == current_has_audio and ext == 'mp4' and current_f.get('ext') != 'mp4':
                            video_formats[height] = f

            # Step 2: Formats ko list mein jodna (High to Low quality sorting)
            for res in sorted(video_formats.keys(), reverse=True):
                f = video_formats[res]
                has_audio = f.get('acodec') not in ['none', None]
                
                # YouTube high quality (1080p+) mein aawaz alag rakhta hai
                audio_tag = "" if has_audio else " (Mute/No Audio)"
                
                if res >= 1080: quality_name = "1080p HD"
                elif res >= 720: quality_name = "720p HD"
                elif res >= 480: quality_name = "480p"
                elif res >= 360: quality_name = "360p"
                else: quality_name = f"{res}p"
                
                video_info["formats"].append({
                    "quality": quality_name + audio_tag,
                    "link": f.get('url')
                })

            # Duplicate qualities ko remove karna
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

            # 🚀 SUPER ULTIMATE FALLBACK: Agar filter ke baad list khali ho jaye 
            if not video_info["formats"]:
                # 1. Check 'requested_formats' (YouTube generally gives combined best streams here)
                for rf in info.get('requested_formats', []):
                    if rf.get('url') and rf.get('url').startswith('http'):
                        note = rf.get('format_note') or rf.get('resolution') or 'Auto'
                        video_info["formats"].append({
                            "quality": f"{note} (Combined)",
                            "link": rf.get('url')
                        })

                # 2. Agar abhi bhi list khali hai, seedha direct URL use karein
                if not video_info["formats"] and info.get('url'):
                    video_info["formats"].append({
                        "quality": "Best Quality Video",
                        "link": info.get('url')
                    })
                
                # 3. Akhiri koshish: Koi bhi safe HTTP link jo image nahi hai
                if not video_info["formats"]:
                    for f in info.get('formats', []):
                        ext = f.get('ext', '')
                        fid = str(f.get('format_id', '')).lower()
                        if f.get('url') and f.get('url').startswith('http') and ext not in ['mhtml', 'webp', 'jpg', 'png', 'gif'] and 'sb' not in fid:
                            video_info["formats"].append({
                                "quality": f"Available Quality ({ext})",
                                "link": f.get('url')
                            })
                            if len(video_info["formats"]) >= 2: # Limit fallback results
                                break

            # Final Duplicate Link Check for Fallbacks
            final_formats = []
            seen_links = set()
            for f in video_info["formats"]:
                if f["link"] not in seen_links:
                    final_formats.append(f)
                    seen_links.add(f["link"])
            
            video_info["formats"] = final_formats

            return {"status": "success", "data": video_info}
            
    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}
