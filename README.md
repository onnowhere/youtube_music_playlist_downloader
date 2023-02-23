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

## Build
To build the standalone executable, you must have Python and `pyinstaller`. Once you do, follow the steps below.

```
python -m pip install -U pyinstaller -r requirements.txt
git submodule init
git submodule update
python scripts/build.py
```

On some systems, you may need to use `py` or `python3` instead of `python`.

## Config
A `.playlist_config.json` file is generated for all album folders and contains the following adjustable fields.


### Options adjustable using the program
- `url`: The URL of the playlist to download songs from (default: set during download)
- `reverse_playlist`: Whether to reverse the order of songs in the playlist when downloading (default: `false`)
- `use_title`: Whether to use the title or track name provided by YouTube where possible as the title for downloaded songs (default: `true`)
- `use_uploader`: Whether to use the uploader or the artist name provided by YouTube where possible as the artist for downloaded songs (default: `true`)
- `use_playlist_name`: Whether to use the playlist or the album name provided by YouTube where possible as the album for downloaded songs (default: `true`)


### Hidden options adjustable in the config file directly
- `name_format`: The name format used to generate file names in yt-dlp output template format (default: `"%(title)s-%(id)s.%(ext)s"`)
- `track_num_in_name`: Whether to include the track number at the start of all file names (default: `true`)
- `audio_format`: The audio format to be used by yt-dlp while downloading songs (default: `"bestaudio/best"`)
- `audio_codec`: The audio codec to be used by yt-dlp while downloading songs (default: `"mp3"`)
- `verbose`: Whether to enable more verbose debug information from yt-dlp (default: `false`)

## License
Licensed under MIT (See [LICENSE](LICENSE))

## Disclaimer
This program was created for educational purposes only. Please respect the copyright of any videos you download. The creator of this program will not be held liable for any copyright violations caused by the usage of this program.