#!/usr/bin/env python3
# YouTube Music Playlist Downloader
# Download a single song

import os
from yt_dlp import YoutubeDL, postprocessor
from urllib.parse import urlparse, parse_qs
from mutagen.id3 import ID3, WOAR, error

class FilePathCollector(postprocessor.common.PostProcessor):
    def __init__(self):
        super(FilePathCollector, self).__init__(None)
        self.file_paths = []

    def run(self, information):
        self.file_paths.append(information['filepath'])
        return [], information

def generate_metadata(file_path, link):
    tags = ID3(file_path)
    tags.add(WOAR(link))
    tags.save(v2_version=3)

def get_url_path(url):
    return urlparse(url).path.rpartition('/')[2]

def get_url_parameter(url, param):
    return parse_qs(urlparse(url).query)[param][0]

def download_video(link):
    directory = os.getcwd()

    ytdl_opts = {
        "outtmpl": f"{directory}/%(id)s.%(ext)s",
        "ignoreerrors": True,
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "5",
        }],
        "geo_bypass": True,
        "quiet": True,
        "external_downloader_args": ["-loglevel", "panic"]
    }

    with YoutubeDL(ytdl_opts) as ytdl:
        file_path_collector = FilePathCollector()
        ytdl.add_post_processor(file_path_collector)
        result = ytdl.download([link])
        file_path = file_path_collector.file_paths[0]
    return result, file_path

url = input("Link: ")
if "youtu.be" in url:
    video_id = get_url_path(url)
else:
    video_id = get_url_parameter(url, "v")
link = f"https://www.youtube.com/watch?v={video_id}"
result, file_path = download_video(link)
generate_metadata(file_path, link)
