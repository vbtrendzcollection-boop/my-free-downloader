app = FastAPI()

# WordPress frontend se connect hone ke liye zaroori hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Mera Free Video Downloader API chal raha hai!"}

@app.get("/get-video")
def get_video(url: str):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            video_info = {
                "title": info.get('title', 'Video Title'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": []
            }

            # Formats nikalna (Jisme Audio aur Video dono ho)
            for f in info.get('formats', []):
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    video_info["formats"].append({
                        "quality": f.get('format_note', 'HD'),
                        "link": f.get('url')
                    })

            return {"status": "success", "data": video_info}
    except Exception as e:
        return {"status": "error", "message": "Video nahi mila."}