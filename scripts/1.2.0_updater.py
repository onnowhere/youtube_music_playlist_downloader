#!/usr/bin/env python3
# YouTube Music Playlist Downloader
# 1.2.0 Updater

import os
from mutagen.id3 import ID3, TIT2, WOAR

def update_link(file_path):
    if not file_path.endswith(".mp3"):
        return

    tags = ID3(file_path)
    if not tags.getall("WOAR"):
        video_title = tags.get("TIT2")
        print(f"Updating link metadata for '{video_title}'...")

        video_id = file_path[-15:-4]
        link = f"https://www.youtube.com/watch?v={video_id}"
        tags.add(WOAR(link))
        tags.save(tags.save(v2_version=3))

def update_links(playlist_name):
    for file_name in os.listdir(playlist_name):
        update_link(os.path.join(playlist_name, file_name))

def get_existing_playlist_names(directory):
    playlist_names = []
    for playlist_name in next(os.walk(directory))[1]:
        config_file = os.path.join(directory, playlist_name, ".playlist_config.json")
        if os.path.exists(config_file):
            playlist_names.append(playlist_name)
    return playlist_names

for playlist_name in get_existing_playlist_names("."):
    update_links(playlist_name)
