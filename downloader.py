import os
import re
import logging
import yt_dlp

from config import COOKIES_FILE

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DL_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DL_DIR, exist_ok=True)


def is_valid_url(url):
    if not isinstance(url, str):
        return False
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(pattern.match(url))


def _opts():
    o = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "retries": 3,
        "socket_timeout": 60,
        "ffmpeg_location": "/usr/bin/ffmpeg",
    }
    if os.path.exists(COOKIES_FILE):
        o["cookiefile"] = COOKIES_FILE
    return o


def get_info(url):
    o = _opts()
    o["skip_download"] = True
    try:
        with yt_dlp.YoutubeDL(o) as ydl:
            info = ydl.extract_info(url, download=False)
            if isinstance(info, dict) and "entries" in info:
                entries = info.get("entries") or []
                if entries:
                    return entries[0]
            return info
    except Exception as e:
        logger.error("get_info: " + str(e))
        return None


def _run(url, opts):
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if isinstance(info, dict) and "entries" in info:
            entries = info.get("entries") or []
            if entries:
                info = entries[0]

        if not isinstance(info, dict):
            raise Exception("Invalid info")

        path = yt_dlp.YoutubeDL(opts).prepare_filename(info)
        if isinstance(path, dict):
            path = path.get("filename", "")

        if path:
            for ext in [".mp3", ".mp4", ".m4a", ".webm", ".mkv"]:
                c = os.path.splitext(path)[0] + ext
                if os.path.exists(c):
                    return c
            if os.path.exists(path):
                return path

        files = sorted(
            [f for f in os.listdir(DL_DIR)],
            key=lambda x: os.path.getmtime(os.path.join(DL_DIR, x)),
            reverse=True)
        if files:
            return os.path.join(DL_DIR, files[0])

        raise Exception("File not found")
    except yt_dlp.utils.DownloadError as e:
        logger.error("Download: " + str(e))
        raise Exception(str(e))


def download_audio(url, chat_id):
    out = os.path.join(DL_DIR, str(chat_id) + "_%(id)s.%(ext)s")
    o = _opts()
    o.update({
        "format": "bestaudio/best",
        "outtmpl": out,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    })
    return _run(url, o)


def download_video(url, chat_id, quality="720"):
    if quality == "360":
        fmt = "best[height<=360][ext=mp4]/best[height<=360]/best"
    elif quality == "480":
        fmt = "best[height<=480][ext=mp4]/best[height<=480]/best"
    elif quality == "720":
        fmt = "best[height<=720][ext=mp4]/best[height<=720]/best"
    elif quality == "1080":
        fmt = "best[height<=1080][ext=mp4]/best[height<=1080]/best"
    else:
        fmt = "best[ext=mp4]/best"

    out = os.path.join(DL_DIR, str(chat_id) + "_%(id)s.%(ext)s")
    o = _opts()
    o.update({
        "format": fmt,
        "outtmpl": out,
        "merge_output_format": "mp4",
    })
    return _run(url, o)


def cleanup(path):
    try:
        if path and isinstance(path, str) and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error("cleanup: " + str(e))
