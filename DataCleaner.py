# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 13:44:51 2020
@author: Andrew Taylor

This file edits the json spotify data. It edits the time stamps and puts the times
relative to the streaming country. The default time zone is Zulu Time Zone (UTC + 0:00).
This code should change the time stamps based on the country I was in at the time
(spotify reports this as "conn_country"). This file also creates datetime objects
to allow easy sorting of streams based on time.
"""
import json
import os
import datetime as dt

def main():
    global sorted_data
    global og_data
    
    og_data = GetData()
    sorted_data = EditData(og_data)
    SaveData(sorted_data)

def GetData():
    data1 = [] # The spotify data
    num = 0
    for n in range(0, 9):
        f = open('endsong_'+str(num)+'.json', encoding = 'utf-8')
        temp = json.load(f)
        for item in temp:
            data1.append(item)
        num += 1
    return data1

def EditData(dataset): #Function that edits the json data
    #global ts
    #global datetime
    loose_codes = [] # Country codes that haven't had their time stamps adjusted
    count = 0
    for dic in dataset:
        ts = dic['ts'][:-1] # Takes the 'Z' off the end of each time stamp.       
        country = dic['conn_country']
        song = dic["master_metadata_track_name"]
        album = dic['master_metadata_album_album_name']
        artist = dic['master_metadata_album_artist_name']
        
        # Check what country the stream is in, and adjust 'hour' to match
        # whatever time I was in at the time 
        if country == 'US' or country == "MX":  #Adjust to EST (-4 hours)
            tshift = -4
        elif country == 'CN': # Adjust to Shanghai Time (+8 hours)
            tshift = 8
        elif country == 'AT' or country == 'IT' or country == 'CH' or country == 'FR':
            tshift = 2
        elif country == 'GB':
            tshift = 1
        else: # Make the code work for other country codes
            if country == 'ZZ': count += 1
            tshift = 0
            outlier = True
            for item in loose_codes:
                if item == country: outlier = False
            if outlier: loose_codes.append(country)
                         
        # Build the datetime object (adjust for time zone)
        datetime = dt.datetime.fromisoformat(ts)
        delta = dt.timedelta(hours = tshift)
        datetime = datetime + delta
        
        # Adjust the song and album names - make them shorter by excluding anything in paranthesis
        new_song = ''
        new_album = ''
        if isinstance(song, str):
            for n in range(len(song)):
                if song[n] == '(': break
                elif song[n] == '/': break 
                else: new_song += song[n]
        else: new_song = song
        if isinstance(album, str):
            for n in range(len(album)):
                if album[n] == '(': break
                else: new_album += album[n]
        else: new_album = album
        
        # Make random adjustments:
        if artist == "Joey Bada$$": artist = "Joey Badass" # $ causes value errors in other code
        
        # Albums that have multiple artists (spotify doesn't note these):
        artist2 = [artist] # Add additional artists to this list
        if new_album == "Drip Harder": artist2 += ["Gunna"]
        elif new_album == "Savage Mode": artist2 += ["Metro Boomin"]
        elif new_album == "UNLOCKED": artist2 += ["Kenny Beats"]
        elif new_album == "Watch The Throne": artist2 += ["Kanye West"]
        elif new_album == "What A Time To Be Alive": artist2 += ["Future"]
        elif new_album == "SUPER SLIMEY": artist2 += ["Young Thug"]
        elif new_album == "Without Warning": artist2 += ["Offset", "Metro Boomin"]
        elif "Young Stoner Life" in artist2: artist2 += ["Young Thug"]
        elif "Black Star" in artist2: artist2 += ["Mos Def", "Talib Kweli"]
        elif "Parliament" in artist2 or "Funkadelic" in artist2:
            artist2 += ["P-Funk"]
        
        #Adjust the values in the dictionary // add new values:
        dic['ts'] = datetime.isoformat()
        dic['datetime'] = datetime
        dic['master_metadata_track_name'] = new_song
        dic['master_metadata_album_album_name'] = new_album
        dic["master_metadata_album_artist_name"] = artist2
        
        
    print("List of unnacounted for country codes (and how many of them are 'ZZ'):")
    print(loose_codes, count) # prints time zones that haven't been adjusted for
    
    # Now sort the dataset based on the datetime object of each stream. Then
    # Remove the datetime objects from the dictionary so they can be saved to .json file
    return_data = sorted(dataset, key = lambda k: k['datetime'])
    for dic in return_data:
        dic['datetime'] = None
    return return_data
        
def SaveData(dataset): # Function that saves the input variable dataset to a .json file
    fout = open('MasterData.json', 'w')
    json.dump(dataset, fout)
    fout.close()
    
                    
if __name__ == '__main__':
    main()
