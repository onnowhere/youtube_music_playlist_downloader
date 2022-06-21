# YouTube Music Playlist Downloader
version = "1.1.0"

import os
import re
import json
import time
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

def write_config(file, config: dict):
    with open(file, "w") as f:
        json.dump(config, f, indent=4)

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

def get_playlist_info(config: dict):
    ytdl_opts = {
        "quiet": True,
        "geo_bypass": True,
        "dump_single_json": True,
        "extract_flat": True,
        "playlistreverse": config["reverse_playlist"]
    }
    with YoutubeDL(ytdl_opts) as ytdl:
        info_dict = ytdl.extract_info(config["url"], download=False)

    return info_dict

def convert_to_jpeg(image):
    with BytesIO() as f:
        image.convert("RGB").save(f, format="JPEG")
        return f.getvalue()
    
def update_track_num(file_path, track_num):
    tags = ID3(file_path)
    tags.add(TRCK(encoding=3, text=str(track_num)))

    tags.save(v2_version=3)
    
def generate_metadata(file_path, link, track_num, playlist_name, config: dict, regenerate_metadata: bool):
    tags = ID3(file_path)
    
    # Generate only if metadata is missing or if explicitly flagged
    metadata_dict = {tag:tags.get(tag) for tag in ["TIT2", "APIC:Front cover", "TRCK", "TPE1", "TALB"]}
    missing_metadata = any([value is None for value in metadata_dict.values()])
    if missing_metadata or regenerate_metadata:
        try:
            # Get song metadata from youtube
            ytdl_opts = {
                "quiet": True,
                "geo_bypass": True
            }
            with YoutubeDL(ytdl_opts) as ytdl:
                info_dict = ytdl.extract_info(link, download=False)
                video_id = info_dict.get("id", None)
                video_title = info_dict.get("title", None)
                artist = info_dict.get("artist", None)
                uploader = info_dict.get("uploader", None)
                album = info_dict.get("album", None)
                thumbnail_url = info_dict.get("thumbnail", None)
        except Exception as e:
            print(f"Unable to gather information for song metadata: {e}")
            return

        try:
            # Generate tags
            print(f"Updating metadata for '{video_title}'...")

            # These tags will not be regenerated in case of config changes
            if metadata_dict["TIT2"] is None:
                tags.add(TIT2(encoding=3, text=video_title))

            if metadata_dict["APIC:Front cover"] is None:
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
                img_data = convert_to_jpeg(img.crop((left, top, right, bottom)))
                tags.add(APIC(3, "image/jpeg", 3, "Front cover", img_data))

            if metadata_dict["TRCK"] is None:
                tags.add(TRCK(encoding=3, text=str(track_num)))

            # These tags can be regenerated in case of config changes
            if config["use_uploader"] or artist is None:
                tags.add(TPE1(encoding=3, text=uploader))
            else:
                tags.add(TPE1(encoding=3, text=artist))

            if config["use_playlist_name"]:
                tags.add(TALB(encoding=3, text=playlist_name))
            elif album is not None:
                tags.add(TALB(encoding=3, text=album))
            else:
                tags.add(TALB(encoding=3, text="Unknown Album"))

            tags.save(v2_version=3)

        except Exception as e:
            print(f"Unable to update metadata: {e}")
        
def download_video(link, album_name, track_num):
    directory = os.path.join(os.getcwd(), album_name)
    ydl = YoutubeDL({
        'outtmpl': f'{directory}/{track_num}. %(title)s-%(id)s.%(ext)s',
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
    return result

def format_file_name(file_name):
    return re.sub(r"[\\/:*?\"<>|]", "_", file_name)

def get_song_file_dict(album_name, print_errors=False):
    file_names = [file_name for file_name in os.listdir(album_name) if file_name.endswith(".mp3")]
    song_file_dict = {}
    for file_name in file_names:
        try:
            song_video_id = file_name[-15:-4] # 11 character video id
            song_file_name = re.sub(r"^[0-9]+. ", "", file_name)
            song_file_path = os.path.join(album_name, file_name)
            song_track_num = int(re.search(r"^[0-9]+", file_name).group())
        except:
            if print_errors:
                print(f"Song file '{file_name}' is in an invalid format and will be ignored")
            continue
        song_file_dict[song_video_id] = {
            "name": Path(song_file_name).stem,
            "file_name": song_file_name,
            "file_path": song_file_path,
            "track_num": song_track_num
        }
    return song_file_dict

def generate_playlist(config: dict, update: bool, regenerate_metadata: bool, current_playlist_name=None):
    # Get list of links in the playlist
    playlist = get_playlist_info(config)
    
    if "entries" not in playlist:
        raise Exception("No videos found in playlist")

    playlist_name = format_file_name(playlist["title"])
    playlist_entries = playlist["entries"]

    # Prepare for downloading
    if update:
        # Check if playlist name changed
        if current_playlist_name is not None and current_playlist_name != playlist_name:
            print(f"Renaming playlist from '{current_playlist_name}' to '{playlist_name}'...")
            os.rename(current_playlist_name, playlist_name)
            if config["use_playlist_name"]:
                # Regenerate metadata to update album tag with playlist name
                regenerate_metadata = True
    else:
        # Create playlist folder
        Path(playlist_name).mkdir(parents=True, exist_ok=True)

    write_config(os.path.join(playlist_name, ".playlist_config.json"), config)
    song_file_dict = get_song_file_dict(playlist_name, print_errors=True)
        
    track_num = 1
    skipped_videos = 0
    updated_video_ids = []
    
    # Download each item in the list
    for i, video_info in enumerate(playlist_entries):
        track_num = i + 1 - skipped_videos
        video_id = video_info["id"]
        link = f"https://www.youtube.com/watch?v={video_id}"

        updated_video_ids.append(video_id)
        song_file_info = song_file_dict.get(video_id)
        
        if song_file_info is not None:
            # Skip downloading audio if already downloaded
            print(f"Skipped downloading '{link}' ({track_num}/{len(playlist_entries) - skipped_videos})")

            song_name = song_file_info["name"]
            song_file_name = song_file_info["file_name"]
            song_file_path = song_file_info["file_path"]
            song_track_num = song_file_info["track_num"]

            # Fix name if mismatching
            file_name = f"{track_num}. {song_file_name}"
            file_path = os.path.join(playlist_name, file_name)
            
            # Update song index if not matched
            if song_track_num != track_num:
                print(f"Reordering '{song_name}' from position {song_track_num} to {track_num}...")
                update_track_num(song_file_path, track_num)
                os.rename(song_file_path, file_path)

            # Generate metadata just in case it is missing
            generate_metadata(file_path, link, track_num, playlist_name, config, regenerate_metadata)

            # Check if video is unavailable
            if video_info["channel_id"] is None:
                # Video title indicates availability of video such as '[Private Video]'
                print(f"The previous song '{song_name}' is unavailable but a local copy exists - {video_info['title']}")
        else:
            try:
                # Download audio if not downloaded
                print(f"Downloading '{link}'... ({track_num}/{len(playlist_entries) - skipped_videos})")

                # Attempt to download video
                result = download_video(link, playlist_name, track_num)
                
                # Check download failed and video is unavailable
                if result != 0 and video_info["channel_id"] is None:
                    # Video title indicates availability of video such as '[Private Video]'
                    raise Exception(f"Video is unavailable - {video_info['title']}")

                # Downloaded video title may not match playlist title due to translations
                # Locate new file by video id and update metadata
                song_file_dict = get_song_file_dict(playlist_name)
                file_path = song_file_dict[video_id]["file_path"]
                generate_metadata(file_path, link, track_num, playlist_name, config, False)
            except Exception as e:
                print(f"Unable to download video: {e}")
                skipped_videos += 1

    # Move songs that are missing (deleted/privated/etc.) to end of the list
    track_num = len(playlist_entries) - skipped_videos + 1
    for video_id in song_file_dict.keys():
        if video_id not in updated_video_ids:
            song_file_info = song_file_dict[video_id]
            song_name = song_file_info["name"]
            song_file_name = song_file_info["file_name"]
            song_file_path = song_file_info["file_path"]
            song_track_num = song_file_info["track_num"]

            if song_track_num == track_num:
                track_num += 1
                continue

            print(f"Moving '{song_name}' from position {song_track_num} to {track_num} due to missing video link...")

            file_name = f"{track_num}. {song_file_name}"
            file_path = os.path.join(playlist_name, file_name)
            
            update_track_num(song_file_path, track_num)
            os.rename(song_file_path, file_path)
            track_num += 1
    
    print("Download finished.")

def get_existing_playlists(directory):
    playlists_data = []
    for playlist_name in next(os.walk(directory))[1]:
        config_file = os.path.join(directory, playlist_name, ".playlist_config.json")
        if os.path.exists(config_file):
            playlist_data = {
                "playlist_name": playlist_name,
                "config_file": config_file,
                "last_updated": time.strftime('%x %X', time.localtime(os.path.getmtime(config_file)))
            }
            playlists_data.append(playlist_data)
    return playlists_data

def get_bool_option_response(prompt, default: bool):
    if default:
        prompt_choice = "Y/n"
    else:
        prompt_choice = "y/N"

    while True:
        response = input(f"{prompt} ({prompt_choice}): ").lower()
        if response == "y" or (default and response == ""):
            return True
        elif response == "n" or (not default and response == ""):
            return False
        else:
            print("Invalid response, please type 'y' or 'n'.")

if __name__ == "__main__":
    print("\n".join([
        "YouTube Music Playlist Downloader v" + version,
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
            config = {}
            update = False
            regenerate_metadata = False
            current_playlist_name = None

            playlists_data = get_existing_playlists(".")
            if len(playlists_data) > 0:
                update = get_bool_option_response("Update an existing playlist?", default=False)
                
            if update:
                # Update existing playlist
                playlists_list = []
                for i, playlist_data in enumerate(playlists_data):
                    playlists_list.append(f"{i + 1}. {playlist_data['playlist_name']} (Last Updated: {playlist_data['last_updated']})")
                print("\n" + "\n".join(playlists_list) + "\n")

                playlist_data = {}
                while True:
                    update_index_raw = input(f"Enter a playlist number to update (1 to {len(playlists_data)}): ")
                    try:
                        update_index = int(update_index_raw) - 1
                        if update_index >= 0 and update_index < len(playlists_data):
                            playlist_data = playlists_data[update_index]
                            break
                    except:
                        pass
                    
                    print("Invalid response, please enter a valid number.")

                current_playlist_name = playlist_data['playlist_name']
                with open(playlist_data["config_file"], "r") as f:
                    config = json.load(f)

                # In case settings were somehow missing
                if 'reverse_playlist' not in config:
                    config["reverse_playlist"] = False
                if 'use_playlist_name' not in config:
                    config["use_playlist_name"] = True
                if 'use_uploader' not in config:
                    config["use_uploader"] = True

                print("\n" + "\n".join([
                    f"Selected playlist: '{current_playlist_name}'",
                    f"URL: {config['url']}",
                    "",
                    f"Playlist settings",
                    f"- Reverse playlist: {config['reverse_playlist']}",
                    f"- Use playlist name for album: {config['use_playlist_name']}",
                    f"- Use uploader instead of artist: {config['use_uploader']}"
                ]) + "\n")

                modify = get_bool_option_response("Modify playlist settings?", default=False)
                if modify:
                    last_use_playlist_name = config["use_playlist_name"]
                    last_use_uploader = config["use_uploader"]

                    config["reverse_playlist"] = get_bool_option_response("Reverse playlist?", default=False)
                    config["use_playlist_name"] = get_bool_option_response("Use playlist name for album?: ", default=True)
                    config["use_uploader"] = get_bool_option_response("Use uploader instead of artist?", default=True)

                    # Metadata needs to be regenerated if the settings have been changed
                    if config["use_playlist_name"] != last_use_playlist_name or config["use_uploader"] != last_use_uploader:
                        regenerate_metadata = True
            else:
                # Download new playlist
                config["url"] = input("Please enter the URL of the playlist you wish to download: ")
                config["reverse_playlist"] = get_bool_option_response("Reverse playlist?", default=False)
                config["use_playlist_name"] = get_bool_option_response("Use playlist name for album?: ", default=True)
                config["use_uploader"] = get_bool_option_response("Use uploader instead of artist?", default=True)

            generate_playlist(config, update, regenerate_metadata, current_playlist_name)
            input("Finished downloading. Press 'enter' to start again or close this window to finish.")
        except KeyboardInterrupt:
            print("\nCancelling...")
            continue
        except Exception as e:
            print(e)
            print("Error encountered while generating. Please try again.")
            continue
