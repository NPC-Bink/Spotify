# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:37:23 2020
@author: Andrew Taylor
@contributor: Joe Scott

Analyzes my music listening habits based on my downloaded Spotify data and
albums rankings Excel sheet.

Reference number for conversation with Emil: 4302579312
The "Escalations Team" handles Spotify data requests that go back farther than 1 year

Things to Add:
    
    Now have info regarding playlists. Each time I add a song to a playlist
    it creates an event (timestamps, etc). May or may not include
    what song/album got added.
    
    AvgArtistRating() currently doesn't use BarGraph() function.
    
    The spotify data does not track songs/albums with multiple artists. Will
    be difficult to fix - could cross reference with Album Ratings spotify sheet
                                                        
    "Obession" rakings - based on how much I initially listen to the song.
                         See how long it takes for my listening of a new
                         song to drop off. How long is song on Top 50? Or
                         see if there's a natural drop off point in streams
                         per week. 
                              
    Animated Charts - Make/research animated graph that shows album/artist
                      stream time as it changes over time
    
    See on average how many streams/minutes I listen to in one sitting
"""
import xlrd
import numpy as np
import matplotlib.pyplot as plt
import statistics as stats
import json
import datetime as dt
import pandas as pd
from matplotlib.animation import FuncAnimation
from IPython.display import HTML

def main():
    global Data  
    global Ratings
    Data, Ratings = GetData()
    TotalStreamTime(Data, start = "2019-12-01", end = "2020-12-01")
    # AvgArtistRating(3) #DOESNT WORK RIGHT NOW
    TimeChart(Data)
    # AnimatedChart(Data)

def GetData(f = "AlbumRatings.xlsx"):
    dataset = [] # The spotify data
    excell = []# My personal album ratings (excel sheet)
    workbook = xlrd.open_workbook(f)
    excell = workbook.sheet_by_index(1)
    f1 = open('MasterData.json', encoding = 'utf-8') #MasterData needs to be created by DataCleaner.py
    temp = json.load(f1)
    for dic in temp:
        datetime = dt.datetime.fromisoformat(dic['ts'])
        dic['datetime'] = datetime #Add datetime object to the dictionary
        dataset.append(dic)
    
    return dataset, excell

def AnimatedChart(dataset):
    # Function that plots an animated bar graph of stream time for songs, albums, artists
    global dframe
    global df2
    global df_rank
    
    prev_date = dt.datetime.fromisoformat("2014-01-01") # Use this reference date to toss out pre-2014 data points
    row = {} # represents a row in the building DataFrame object. Each row is a unique date and holds the sum of each artists' total stream time
    dframe = pd.DataFrame.from_dict(row)
    dates = []
    for dic in dataset:
        artist = dic['master_metadata_album_artist_name']
        album = dic['master_metadata_album_album_name']
        dtime = dic['datetime']
        stream = dic['ms_played'] / 3600000
        
        if isinstance(album, str) and stream > 0 and dtime > prev_date: #Throws out bad data (local files and 2013)
            for name in artist:
                if name in row:
                    row[name] += stream
                else: 
                    row[name] = stream
            if dtime.date() > prev_date.date():
                row['Date'] = str(dtime.date())
                dates += str(dtime.date())
                dframe = dframe.append(row, ignore_index = True)
                prev_date = dtime
                
    dframe.set_index('Date', inplace=True) # Make each row label that row's unique date
    dframe.fillna(0, inplace=True) # Replace Na / NaN values with 0
    
    # Make new dataframes with interpolated values (ranked and unranked). Interpolated ranks needed for animation of bars changing ranks
    df2 = dframe.reset_index()
    df2.index = df2.index * 4
    df2 = df2.reindex(range(df2.index[-1] + 1)) # generates blank rows to be filled w/ interpolated values
    df2['Date'] = df2['Date'].fillna(method='ffill') # Don't interpolate dates, copy those
    df2 = df2.set_index('Date') # Reset the index to the dates
    df_rank = df2.rank(axis=1, method = 'first') # Make the ranked DataFrame
    df_rank = df_rank.interpolate() # Interpolate values for blank rows
    df2 = df2.interpolate() # Interpolate values for blank rows
    

    #%% Make the animated graph (v3: with animation)
 
    def init(): #Init function for animation
        ax.clear()
        ax.set_facecolor('.8')
        ax.tick_params(labelsize=3.5, length=0)
        ax.grid(True, axis='x', color='white')
        ax.set_axisbelow(True)
        [spine.set_visible(False) for spine in ax.spines.values()]
        
    def update(i): #Update function for the animation
        for bar in ax.containers:
            bar.remove()
        y1 = df_rank.iloc[i] # all rank values for given date
        s1 = df2.iloc[i] # all names and stream times for given date
        cutoff = len(y1) - 15 # The cutoff ranking
        y = [] # ONLY top 15 rank values for given date
        s = pd.Series() # ONLY top 15 names and stream times for given date
        for name, val in y1.items(): # Loop that populates y and s
            if val >= cutoff:
                y.append(val-cutoff) # subtract cutoff to make y full of values 0-15
                s = s.append(pd.Series(s1.loc[name], [name]))
        ax.barh(y=y, width=s.values, color=colors, tick_label=s.index)
        ax.set_title(df2.index[i], fontsize='smaller')
        ax.set_xlabel("Stream Time (hrs)")
        
    fig = plt.Figure(figsize=(4, 2.5), dpi=144)
    ax = fig.add_subplot()
    colors = plt.cm.tab20b(range(15)) # Assings colors to each bar in graph
    anim = FuncAnimation(fig=fig, func=update, init_func=init, frames=len(df2), 
                         interval = 10, repeat=False) #Function that actually makes the animation
    HTML(anim.to_html5_video())
    anim.save("ArtistStreamTime.mp4")
        
        
#%%
                
def TimeChart(dataset):
    # Function that makes a bar graph showing when I listen to music on an 
    # hour to hour basis and a month to month basis. It also compares daily
    # listening habits of weekdays vs. weekends. 
    
    hours = [] # List where each index is a list that contains stream's hour (from timestamp) and ms played
    months = [] # List where each index is a stream's month (from timestamp) and ms played
    hours_weekend = [] # same thing as hours but only for weekends
    hours_week = [] # same thing as hours but only for weekdays
    g_hours = [] # compiled list of each hour and its total stream time (used in graph)
    g_months = [] # compiled list of each month and its total stream time (used in graph)
    g_hours_week = []
    g_hours_end = []
    
    # Grab relevent data:
    for i in range(len(dataset)):
        stream = dataset[i] 
        datetime = stream.get('datetime')
        streamInfo = [stream.get('ms_played') / 3600000] # convert miliseconds to hours
        weekday = datetime.isoweekday() # Monday = 1, Sunday = 7
        hours.append([datetime.hour, streamInfo])
        months.append([datetime.month, streamInfo])
        if weekday < 6:
            hours_week.append([datetime.hour, streamInfo])
        else: hours_weekend.append([datetime.hour, streamInfo])
        
    
    # Compile all the stream times by key (hour, month)
    compiled_hours = ReduceByKey(hours)
    compiled_months = ReduceByKey(months)
    comp_hours_week = ReduceByKey(hours_week)
    comp_hours_end = ReduceByKey(hours_weekend)
   
    # Get total amount of hours since the earliest date in the json data
    start = dataset[0]['datetime']
    end = dataset[len(dataset)-1]['datetime']
    delta = end - start
    total_hours = (delta.days * 24 + delta.seconds / 3600)
    
    # Now use compiled list to get sum of stream times for each key (hour, month)
    for i in range(len(compiled_hours)):
        if i < len(compiled_months):
            g_months.append([compiled_months[i][0], sum(compiled_months[i][1])])
        g_hours.append([compiled_hours[i][0], sum(compiled_hours[i][1])*60/(total_hours/24)])
        # ^ Divide by 24 so total_hours is how many hours of each hour has passed
        g_hours_end.append([comp_hours_end[i][0], sum(comp_hours_end[i][1])*60/((2/7)*total_hours/24)])
        # ^ The added (2/7) adjusts the total hours to only represent the total weekend horus
        g_hours_week.append([comp_hours_week[i][0], sum(comp_hours_week[i][1])*60/((5/7)*total_hours/24)])
   
    # Sort the lists before graphing    
    g_months.sort(key=lambda x: x[0])
    g_hours.sort(key=lambda x: x[0])
    g_hours_end.sort(key=lambda x: x[0])
    g_hours_week.sort(key=lambda x: x[0])
    
    # Graph the results
    ax = BarGraph(g_months, 12, "Stream Time Per Month", "Stream Time (hrs)",
             ylimit = (0, 650), xlabel = "Month of the Year")
    ax.tick_params(axis = 'x', labelrotation = 0, labelsize = 12)
    ax.set_xticks(list(range(1,13)))
      
    # Figure to compare weekdays and weekends in terms of music listened to per hour
    fig, axs = plt.subplots(2,1, figsize = (16,9))
    fig.suptitle("Average Minutes per Hour Spent Listening to Music", fontsize = 16)
    for i in range(2):
        key = [] # X coordinates of the bars
        height = [] # Y coordinates of the bars
        for n in range(24):
            key.append(n)
            if i == 0: height.append(g_hours_week[n][1])
            else: height.append(g_hours_end[n][1])
        bars = axs[i].bar(key,height, align = 'edge')
        axs[i].set_xticks(list(range(0,25)))
        axs[i].set_yticks(list(range(0,11)))
        axs[i].grid(axis = 'y')
        axs[i].set_ylabel("Minutes per Hour", fontsize = 12)
        if i == 0: axs[i].set_title("Weekdays", fontsize = 14)
        else: 
            axs[i].set_title("Weekends", fontsize = 14)
            axs[i].set_xlabel("Time of Day (military time)", fontsize = 14)
        for bar in bars: #Loop that adds labels to bars
            value = round(bar.get_height(), 1)
            axs[i].annotate('{}'.format(value),
                        xy=(bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
            
    # # Same figure but doesn't seperate weekdays and weekends:        
    # ax = BarGraph(g_hours, 24, "Average Minutes per Hour Spent Listening to Music", 
    #               "Minutes", xlabel = "Time of Day (military time)",
    #               ylimit = (0, 10), alignment = 'edge')
    # ax.tick_params(axis = 'x', labelrotation = 0, labelsize = 12)
    # ax.set_xticks(list(range(0,25)))
        
def AvgArtistRating(minAlbums):
    # Calculates and displays the average album score for each artist. Will
    # only plot artists whose number of albums is >= minAlbums
    
    artist_ratings = [] # List of artists and all of their album ratings
    album_ratings = [] # List of albums and their ratings and stream times
    
    newArtist = True #Initialize as true for the first artist
    for i in range(1, Ratings.nrows): 
        artists = Ratings.cell_value(i,1).split(',') 
        rating = Ratings.cell_value(i,5)
        album = Ratings.cell_value(i,0)
        album_ratings.append([album, rating])
        
        #If there are multiple artists for an album split them up:
        for name in artists:
            if name[0] == " ": #Get rid of spaces before artist name
                tempName = ""
                for i in range(1, len(name)):
                    tempName += name[i]
                name = tempName
            # Now check if it's a new artist:
            for n in range(len(artist_ratings)):
                if name == artist_ratings[n][0]:
                    artist_ratings[n][1].append(rating)
                    artist_ratings[n][2].append(album)
                    newArtist = False
                    break
                elif n == len(artist_ratings) - 1:
                    newArtist = True      
            if newArtist:
                lst = [name, [rating], [album]]
                artist_ratings.append(lst)

    # Get the average album rating for each artist:
    graph_results = []
    for i in range(len(artist_ratings)):
        if len(artist_ratings[i][1]) >= minAlbums:
            graph_results.append([artist_ratings[i][0], 
                                  stats.mean(artist_ratings[i][1]),
                                  stats.stdev(artist_ratings[i][1])])    
    graph_results.sort(reverse = True, key = lambda x: x[1])
    
    # Now get each albums total stream time from the Spotify dataset
    spotify_data = []
    for dic in Data:
        album1 = dic["master_metadata_album_album_name"] #already a variable named 'album'
        time = [dic['ms_played'] / 3600000] # Convert ms to hours
        spotify_data.append([album1, time])
    spotify_comp = ReduceByKey(spotify_data) # Compile all the album stream times
    spotify_sum = []
    for lst in spotify_comp: # Sum up the stream times for each album
        if isinstance(lst[0], str): # Tosses out the NoneType data points
            spotify_sum.append([lst[0], sum(lst[1])])
            
    # Now put the stream times from 'spotify_sum' into 'album_ratings'
    for lst in album_ratings:
        for item in spotify_sum:
            if lst[0] == item[0]: # Check that the album titles are the same
                lst.append(item[1])
                
    # Seperate out the albums that don't have any spotify data (problem children)
    ratings_times = [] # Final list comparing ratings and stream times (used in graph)
    problems = []
    for lst in album_ratings:
        if len(lst) < 3:
            problems.append(lst[0])
        else:
            ratings_times.append([str(lst[1]), [lst[2]]])
    print("There is no Spotify data for these albums:")
    print(problems)
    ratings_times_comp = ReduceByKey(ratings_times)
    ratings_times_comp.sort(key=lambda x:x[0])
    ratings_times_comp.append(ratings_times_comp[0]) # Janky strats to override the fact that sort() treats '10' as less than '5'
    ratings_times_comp.remove(ratings_times_comp[0])
    
    # Make a numpy array out of ratings_times_comp (used for boxplot)
    
        
    # Graph the average album rating for each artist:
    artistName = []
    avgScore = []
    standardDev = []
    for i in range(len(graph_results)):
        artistName.append(graph_results[i][0])
        avgScore.append(graph_results[i][1])  
        standardDev.append(graph_results[i][2])
    fig = plt.figure(figsize = (16,9))
    ax = fig.add_subplot(111)
    bars = ax.bar(artistName, avgScore)
    ax.set_ylim(6, 10)
    ax.set_ylabel('Average Album Rating', fontsize = 14)
    ax.set_title("Average Album Score per Artist", fontsize = 20)
    ax.tick_params(axis = 'x', labelrotation = 75, labelsize = 8)
    ax.tick_params(axis = 'y', labelsize = 12)
    ax.grid(axis = 'y')
    for bar in bars: # Loop to add labels to each bar
        height = round(bar.get_height(),2)
        ax.annotate('{}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
        
    # Plot album ratings vs. stream time:
    ratings = []
    streamTimes = []
    for lst in album_ratings:
        if len(lst) == 3:
            ratings.append(lst[1])
            streamTimes.append(lst[2])
    xticks = [] # Have to make a list for the x tick marks // Couldn't make it work with range() :(
    num = int(min(ratings))
    while num < 10.1:
        xticks.append(num)
        num += 0.5
    fig = plt.figure(figsize = (16,9))
    ax = fig.add_subplot(111)
    ax.scatter(ratings,streamTimes)
    ax.set_xticks(xticks)
    ax.set_title("Album Ratings vs. Album Stream Times", fontsize = 20)
    ax.set_xlabel("Album Rating (1-10)", fontsize = 14)
    ax.set_ylabel("Total Stream Time (hrs)", fontsize = 14)
    ax.set_ylim(0,100)
    ax.grid(axis='y')


def TotalStreamTime(data, start = 1, end = 1):
    # Function that will calculate and graph the total stream time of each artist,
    # album, and song. The variable 'top' determins how many of the top artists
    # will be graphed on the bar graph. The optional variables 'start' and 'end'
    # specify a range of dates to analyze spotify streams. They should be dates
    # in iso format (yyyy-mm-dd)
    # Note: the spotify data counts the song/album/artist name of local files as
    # null. Currently this function just tosses those data values out.
    
    artistList = [] # list of all the artists and their stream times (not combined):
    albumList = [] # list of all the albums and their.....
    songList = [] # list of all the songs.....
    artists = [] # the final lists used for graphing:
    albums = [] 
    songs = []
    
    
    # First grab the input variables 'start' and 'end' and turn them into datetimes.
    # They are by default integers so the following if statement fails:
    if isinstance(start, str) and isinstance(end, str):
        d1 = dt.datetime.fromisoformat(start)
        d2 = dt.datetime.fromisoformat(end)
    else: 
        d1 = data[0]['datetime']
        d2 = data[-1]['datetime']
    
    # Then grab the datapoints in-between the two datetimes:
    for i in range(len(data)):        
        artist = data[i].get("master_metadata_album_artist_name")
        album = data[i].get("master_metadata_album_album_name")
        song = data[i].get("master_metadata_track_name")
        dtime = data[i].get("datetime")
        streamTime = [data[i].get('ms_played') / 3600000] # convert miliseconds to hours
        if isinstance(song, str) and dtime > d1 and dtime < d2:
            for n in range(len(artist)): # for albums with multiple artists attribute the stream time to each artist seperately
                artistList.append([artist[n], streamTime])    
                if n == 0: # If statement to avoid double counting albums and songs
                    albumList.append([album, streamTime])
                    songList.append([song, streamTime])
    
    # Compile all the stream times by key (artist, album, song)    
    newList1 = ReduceByKey(artistList)
    newList2 = ReduceByKey(albumList)
    newList3 = ReduceByKey(songList)
    
    # Sum up the compiled list to get the total stream time for each key
    for i in range(len(newList3)):
        if i < len(newList1):
            artists.append([newList1[i][0], sum(newList1[i][1])])
        if i < len(newList2):
            albums.append([newList2[i][0], sum(newList2[i][1])])
        songs.append([newList3[i][0], sum(newList3[i][1])])        
    artists.sort(key=lambda x: x[1], reverse=True) # Sorts the lists by time listened to
    albums.sort(key=lambda x: x[1], reverse=True)
    songs.sort(key=lambda x: x[1], reverse=True)
    
    

    # Graph the results, first by figuring out what the ylimit will be for each graph
    s_top = round(songs[0][1]) + round(songs[0][1])/4
    al_top = round(albums[0][1]) + round(albums[0][1])/4
    ar_top = round(artists[0][1]) + round(artists[0][1])/4
    
    ax = BarGraph(artists, 20, "Total Artist Stream Times", "Stream Time (hrs)",
             ylimit = (0, ar_top))
    ax = BarGraph(albums, 20, "Total Album Stream Times", "Stream Time (hrs)",
              ylimit = (0, al_top))
    ax = BarGraph(songs, 20, "Total Song Stream Times", "Stream Time (hrs)",
              ylimit = (0, s_top))

               
def BarGraph(data, bars, title, ylabel, ylimit, xlabel = '', alignment = 'center', labels = True):
    # Function that creates a bar graph. The input variable "data" should be a list
    # of lists, where each item in the list represents a single bar and that single
    # bar's height.
    key = []
    height = []
    for n in range(bars):
        key.append(data[n][0])
        height.append(data[n][1])
    fig = plt.figure(figsize = (16,9))
    ax = fig.add_subplot(111)
    bars = ax.bar(key, height, align = alignment)
    ax.set_ylim(ylimit)
    ax.set_ylabel(ylabel, fontsize = 14)
    ax.set_xlabel(xlabel, fontsize = 16)
    ax.set_title(title, fontsize = 20)
    ax.tick_params(axis = 'x', labelrotation = 70, labelsize = 8)
    ax.tick_params(axis = 'y', labelsize = 12)
    ax.grid(axis = 'y')
    # Loop to add labels to each bar:
    if labels:
        for bar in bars:
            value = round(bar.get_height(), 2)
            ax.annotate('{}'.format(value),
                        xy=(bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
    plt.show()
    return ax

def ReduceByKey(lst):
    d = dict()
    for key, sublist in lst:
        d.setdefault(key, []).extend(sublist)
    return list(d.items())


if __name__ == '__main__':
    main()
