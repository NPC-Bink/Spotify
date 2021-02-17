# Spotify
Code that analyzes spotify streaming data. To use must have already downloaded your personal spotify data. Link to download spotify data: https://www.spotify.com/ca-en/account/privacy/#_=_

Note: By default Spotify only sends your last 1 year of data, but if you chat with a representative they can send you your entire streaming history.

Use of my code is pretty simple. One file (DataCleaner.py) cleans up the raw data. Mostly all it does is compile all the various data files into one massive file and adds datetime objects to each stream so you can organize them by time.

The other file (MusicData.py) does all the analytics. I built it for personal use so if you're trying to use it might have to rename data files to match what the code expects. 
