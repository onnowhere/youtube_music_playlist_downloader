#!/usr/bin/env python3

# Allow direct execution
import os
import sys

if 'idlelib.run' in sys.modules and sys.stdin is not sys.__stdin__:
    print("Do not run this from IDLE. Run this script from a console instead.")
    sys.exit()

# Ensure executing from script dir
os.chdir(os.path.realpath(os.path.dirname(__file__)))
    
# Make lazy extractors
os.chdir('../scripts/yt-dlp-master')
os.system('python devscripts/make_lazy_extractors.py')

# Move to main directory
os.chdir('../../')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PyInstaller.__main__ import run as run_pyinstaller

# Options to build program
opts = ['-F', 'youtube_music_playlist_downloader.py']

# Options to build yt-dlp with program
opts = [
    '--upx-exclude=vcruntime140.dll',
    '--noconfirm',
    '--additional-hooks-dir=scripts/yt-dlp-master/yt_dlp/__pyinstaller',
    *opts,
    'scripts/yt-dlp-master/yt_dlp/__main__.py',
]

# Run PyInstaller
print(f'Running PyInstaller with {opts}')
run_pyinstaller(opts)
