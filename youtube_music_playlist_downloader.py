# YouTube Music Playlist Downloader

import re
import os
import requests
import subprocess
from PIL import Image
from io import BytesIO
from pathlib import Path
from yt_dlp import YoutubeDL
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TRCK, TALB, USLT, error

# ID3 info:
# APIC: picture
# TIT2: title
# TPE1: artist
# TRCK: track number
# TALB: album
# USLT: lyric

def check_ffmpeg():
    ffmpeg_available = True
    try:
        subprocess.check_output(['ffmpeg', '-version'])
    except Exception as e:
        ffmpeg_available = False
    if not ffmpeg_available:
        print("\n".join([
            "[ERROR] ffmpeg not found. Please ensure ffmpeg is installed",
            "and you have included it in your PATH environment variable.",
            "Download ffmpeg here: https://www.ffmpeg.org/download.html.",
            "-----------------------------------------------------------",
        ]))
    return ffmpeg_available

def getPlaylistInfo(url, reverse_playlist=False):
    ytdl_opts = {
        "quiet": True,
        "geo_bypass": True,
        "dump_single_json": True,
        "extract_flat": True,
        "playlistreverse": reverse_playlist
    }
    with YoutubeDL(ytdl_opts) as ytdl:
        info_dict = ytdl.extract_info(url, download=False)

    return info_dict

def convertToJpeg(image):
    with BytesIO() as f:
        image.convert("RGB").save(f, format="JPEG")
        return f.getvalue()
    
def update_track_num(file_path, track_num):
    tags = ID3(file_path)
    tags.add(TRCK(encoding=3, text=str(track_num)))

    tags.save(v2_version=3)
    
def generate_metadata(file_path, link, track_num, playlist_to_name: bool, playlist_name):
    tags = ID3(file_path)
    
    # Generate only if metadata is missing
    check_title = tags.get("TIT2")
    if check_title is None:
        ytdl_opts = {
            "quiet": True,
            "geo_bypass": True
        }
        with YoutubeDL(ytdl_opts) as ytdl:
            info_dict = ytdl.extract_info(link, download=False)
            video_id = info_dict.get("id", None)
            video_title = info_dict.get("title", None)
            uploader = info_dict.get("artist", None) or info_dict.get("uploader", None)
            album = info_dict.get("album", None)
            thumbnail_url = info_dict.get("thumbnail", None)
            
        print("Updating metadata for '{0}'...".format(video_title))

        # Generate thumbnail
        img = Image.open(requests.get(thumbnail_url, stream=True).raw)
        width, height = img.size
        half_width = width / 2
        half_height = height / 2
        min_offset = min(half_width, half_height)
        left = half_width - min_offset
        right = half_width + min_offset
        top = half_height - min_offset
        bottom = half_height + min_offset
        img_data = convertToJpeg(img.crop((left, top, right, bottom)))

        # Generate tags
        tags.add(APIC(3, "image/jpeg", 3, "Front cover", img_data))
        tags.add(TIT2(encoding=3, text=video_title))
        if album != None and playlist_to_name:
            tags.add(TALB(encoding=3, text=playlist_name))
        elif album != None:
            tags.add(TALB(encoding=3, text=playlist_name))
        tags.add(TPE1(encoding=3, text=uploader))
        tags.add(TRCK(encoding=3, text=str(track_num)))

        tags.save(v2_version=3)
        
def download_video(link, album_name, track_num):
    ydl = YoutubeDL({
        'outtmpl': '{0}/{1}. %(title)s-%(id)s.%(ext)s'.format(os.path.join(os.getcwd(), album_name), track_num),
        'ignoreerrors': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'geo_bypass': True,
        'quiet': True,
        'external_downloader_args': ['-loglevel', 'panic'],
    })

    result = ydl.download([link])
    return

def format_file_name(file_name):
    return re.sub(r"[\\/:*?\"<>|]", "_", file_name)

def get_song_file_dict(album_name, print_errors=False):
    file_names = [file_name for file_name in os.listdir(album_name) if file_name.endswith(".mp3")]
    song_file_dict = {}
    for file_name in file_names:
        try:
            song_video_id = file_name[-15:-4] # 11 character video id
            song_name = re.sub(r"^[0-9]+. ", "", file_name)
            song_track_num = int(re.search(r"^[0-9]+", file_name).group())
        except:
            if print_errors:
                print("Song file {0} is in an invalid format and will be ignored".format(file_name))
            continue
        song_file_dict[song_video_id] = {
            "song_name": song_name,
            "track_num": song_track_num,
            "file_path": os.path.join(album_name, file_name)
        }
    return song_file_dict

def generate_playlist(url, reverse_playlist: bool = False, playlist_to_name: bool = True):
    # Get list of links in the playlist
    playlist = getPlaylistInfo(url, reverse_playlist)
    
    if "entries" not in playlist:
        raise Exception("No videos found in playlist")

    playlist_name = format_file_name(playlist["title"])
    playlist_entries = playlist["entries"]

    # Prepare for downloading
    Path(playlist_name).mkdir(parents=True, exist_ok=True)
    song_file_dict = get_song_file_dict(playlist_name, print_errors=True)
        
    track_num = 1
    updated_video_ids = []
    
    # Download each item in the list
    for i, video_info in enumerate(playlist_entries):
        track_num = i + 1
        video_id = video_info["id"]
        link = "https://www.youtube.com/watch?v={0}".format(video_id)

        updated_video_ids.append(video_id)
        song_file_info = song_file_dict.get(video_id)
        
        if song_file_info is not None:
            # Song is already downloaded
            song_name = song_file_info["song_name"]
            song_track_num = song_file_info["track_num"]
            song_file_path = song_file_info["file_path"]

            # Fix name if mismatching
            file_name = "{0}. {1}".format(track_num, song_name)
            file_path = os.path.join(playlist_name, file_name)
            
            # Update song index if not matched
            if song_track_num != track_num:
                print("Reordering '{0}' from position {1} to {2}...".format(song_name, song_track_num, track_num))
                update_track_num(song_file_path, track_num)
                os.rename(song_file_path, file_path)

            # Generate metadata just in case it is missing
            generate_metadata(file_path, link, track_num, playlist_to_name, playlist_name)
            
            # Skip downloading audio if already downloaded
            print("Skipped downloading '{0}' ({1}/{2})".format(link, track_num, len(playlist_entries)))
        else:
            try:
                # Download audio if not downloaded
                print("Downloading '{0}'... ({1}/{2})".format(link, track_num, len(playlist_entries)))
                download_video(link, playlist_name, track_num)

                # Downloaded video title may not match playlist title due to translations
                # Locate new file by video id and update metadata
                song_file_dict = get_song_file_dict(playlist_name)
                file_path = song_file_dict[video_id]["file_path"]
                generate_metadata(file_path, link, track_num, playlist_to_name, playlist_name)
            except Exception as e:
                print("Unable to download video:", e)

    # Move songs that are missing (deleted/privated/etc.) to end of the list
    track_num = len(playlist_entries) + 1
    for video_id in song_file_dict.keys():
        if video_id not in updated_video_ids:
            song_file_info = song_file_dict[video_id]
            song_name = song_file_info["song_name"]
            song_track_num = song_file_info["track_num"]
            song_file_path = song_file_info["file_path"]

            if song_track_num == track_num:
                track_num += 1
                continue

            print("Moving '{0}' from position {1} to {2} due to missing video link...".format(song_name, song_track_num, track_num))

            file_name = "{0}. {1}".format(track_num, song_name)
            file_path = os.path.join(playlist_name, file_name)
            
            update_track_num(song_file_path, track_num)
            os.rename(song_file_path, file_path)
            track_num += 1
    
    print("Download finished.")

if __name__ == "__main__":
    print("\n".join([
        "YouTube Music Playlist Downloader",
        "-----------------------------------------------------------",
        "This program automatically downloads & updates a local copy",
        "of any YouTube playlist in the form of a music album folder",
        "- Songs are stored in album folders named by playlist title",
        "- Existing albums are updated with any new or missing songs",
        "- Songs no longer in the playlist are moved to end of album",
        "- Song metadata is automatically generated using video info",
        "- Metadata includes Title, Artists, Album, and Track Number",
        "- Cover art for songs are created by using video thumbnails",
        "",
        "[NOTE] This program and ffmpeg may be blocked by antivirus.",
        "If you run into any issues, you can try adding this program",
        "and your ffmpeg folder to the exclusions of your antivirus.",
        "-----------------------------------------------------------",
    ]))
    
    while True:
        try:
            check_ffmpeg()
            url = input("Please enter the url of the playlist you wish to download: ")
            reverse_playlist = False
            while True:
                response = input("Reverse playlist? (y/n): ").lower()
                if response == "y":
                    reverse_playlist = True
                    break
                elif response == "n" or response == "":
                    reverse_playlist = False
                    break
                else:
                    print("Invalid response, please type 'y' or 'n'")
            playlist_to_name = False
            while True:
                response = input("Use playlist name for album? (Y/n): ").lower()
                if response == "y":
                    playlist_to_name = True
                    break
                elif response == "n":
                    playlist_to_name = False
                    break
                else:
                    print("Invalid response, please type 'y' or 'n'")
            generate_playlist(url, reverse_playlist, playlist_to_name)
            input("Finished downloading. Press 'enter' to start again or close this window to finish.")
        except KeyboardInterrupt:
            print("\nCancelling...")
            continue
        except Exception as e:
            print(e)
            print("Error encountered while generating. Please try again.")
            continue
