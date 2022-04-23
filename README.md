# YouTube Music Playlist Downloader

This program automatically downloads & updates a local copy
of any YouTube playlist in the form of a music album folder
- Songs are stored in album folders named by playlist title
- Existing albums are updated with any new or missing songs
- Songs no longer in the playlist are moved to end of album
- Song metadata is automatically generated using video info
- Metadata includes Title, Artists, Album, and Track Number
- Cover art for songs are created by using video thumbnails

[NOTE] This program and ffmpeg may be blocked by antivirus.
If you run into any issues, you can try adding this program
and your ffmpeg folder to the exclusions of your antivirus.

## Requirements
- FFMPEG: Make sure you can run `ffmpeg` from the command line. If you are on Windows check your PATH.

## Install
For Windows, you can directly download the executable from the following link:

[![Windows](https://img.shields.io/badge/-Windows_x64-blue.svg?style=for-the-badge&logo=windows)](https://github.com/onnowhere/youtube_music_playlist_downloader/releases/latest/download/youtube_music_playlist_downloader.exe)

Alternatively, you can clone and install from source with Python 3.
```
git clone https://github.com/onnowhere/youtube_music_playlist_downloader
cd youtube_music_playlist_downloader
pip install -r requirements.txt
```

## Usage
Double click the executable to run and follow the instructions that are presented.

If using the source files, double click the file to run with Python or run from command line.
```
python youtube_music_playlist_downloader.py
```

## License
Licensed under MIT (See [LICENSE](LICENSE))

## Disclaimer
This program was created for educational purposes only. Please respect the copyright of any videos you download. The creator of this program will not be held liable for any copyright violations caused by the usage of this program.