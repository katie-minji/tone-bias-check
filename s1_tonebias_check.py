# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 12:42:07 2022

@author: Katie Kim
"""
# =============================================================================
# 
# PLEASE READ THIS!!!
# 
# 
# << Instructions >>
# 
# Purpose: 
# This code is use to check tone bias (2Hz vs 8Hz) in stage1 before the fear conditioning with the 2Hz tone. 
# This code plots 3 subplots, [1: 2Hz null and hitrate], [2: 8Hz null and hitrate], [3: 2Hz and 8Hz hitrate comparison]
# 
# Batching == Possible!: (options) 
# [1: by mouse --> e.g. wt871_N folder: all stage 1 training session file for wt871_N mouse], 
# [2: specific session --> e.g. 09_21_2022___09_44_12 file: specific training session file in stage 1] --> can't get session!
# --> additional instruction: change 'batch' on the first line of the code to 'y' (#1/2) or 'n' (#3)
# 
# To access:
# [SooB --> Projects --> Association --> COHORT --> MOUSE --> TEXT FILE]
# 
# =============================================================================


import pandas as pd
from tkinter import filedialog as fd
import numpy as np
import matplotlib.pyplot as plt
import os
import time


    
def file_extraction():
    if batch == 'n':  #not batching, input==file
        path = fd.askopenfilename() 
        head, tail = os.path.split(path)
        mylist = [(head, tail)]
        mouselist = [x for x in path.split('/') if 'wt' in x]
        everything = list(os.walk(head))
        for dirpath, dirnames, filenames in everything:
            filenames_list = [x for x in filenames]
            filenames_list.sort()
            i=0
            for x in filenames_list:
                if x == tail:
                    session = 'S' + str(i+1)
                if x[0:10] == tail[0:10]:
                    i+=1
    else:
        maindir = fd.askdirectory()
        everything = list(os.walk(maindir))  #list of folder, subfolder, files
        filelist = []
        dirlist = []
        for dirpath, dirnames, filenames in everything:
            if 'wt' in os.path.basename(everything[0][0]):
                mouselist = [os.path.basename(everything[0][0])]
            else:
                mouselist = [x for x in everything[0][1]]  #list mouse in cohort
            if os.path.basename(dirpath) == 'Stage1':  #files in Stage1
                flist = [x for x in filenames if x.endswith('.txt')]
                filelist.append(flist)
                dirlist.append(dirpath)
        mylist = list(zip(dirlist,filelist))  #combine directory and files into tuples
        session = 0
    files = {mouselist[i]: mylist[i] for i in range(len(mouselist))}  #make dictionary key=mouse, value=directory&files

    return files, session
    

def organizing(files, session):
    df_dict = {}
    final_df_dict = {}
    for mouse in files:
        if batch == 'n': 
            day_series = [files[mouse][1][0:10].replace('_', '-')]
            dir_series = os.path.normpath(os.path.join(files[mouse][0], files[mouse][1]))
            df_dict[mouse] = pd.DataFrame({'day': day_series, 'session': np.asarray([session]), 'directory': np.asarray([dir_series])}) 
            df_mouse = df_dict[mouse]
        else:
            dir_series = []
            day_series = np.asarray([y.replace('_', '-') for y in [x[0:10] for x in files[mouse][1]]])
            time_series = np.asarray([x[13:21] for x in files[mouse][1]])
            for file in files[mouse][1]:
                dir_series.append(os.path.normpath(os.path.join(files[mouse][0], file)))            
            df_dict[mouse] = pd.DataFrame({'day': day_series, 'time': time_series, 'directory': dir_series})
            df_mouse = df_dict[mouse]
            session_list = []
            count_df = df_mouse.groupby('day').size()
            for day, day_df in df_mouse.groupby('day'):
                day_df.sort_values(by=['time'])
                session_per_day = count_df[day]
                for i in range(session_per_day):
                    session_list.append('S'+str(i+1))
            df_mouse.insert(2, "session", np.asarray(session_list))
            del df_mouse['time']
        final_df_dict.update({mouse: df_mouse})
            
    return final_df_dict


def results_df(row):  # select file
    original_file = row['directory']
    with open(original_file) as f:
        lines = [line.rstrip() for line in f.readlines()]    
    # create two list of starting point and terminal point   
    start_list = [i for i,x in enumerate(lines) if "stim_presentation:" in lines[i]]
    terminal_list = [i for i,x in enumerate(lines) if 'ITI' and 'START:' in lines[i]]
    # for lines within presentation (between starting point and terminal point), list all words within
    i = 0  #counter
    trial_words_list = {}  #empty dictionary
    while i < len(start_list):  #for presentation #
        presentation = ' '.join(lines[start_list[i]:terminal_list[i]])
        trial_words_list[i+1] = presentation
        i+=1
    i = 1
    res_array = np.empty(shape=(0, 4))  #empty array, holds results
    while i <= len(trial_words_list):
        tone = 8 if ('tone 8' in trial_words_list[i]) else 2  #record tone
        check_null = False if 'Window' in trial_words_list[i] else True  #check if null or hit/miss
        if check_null == True:  #if null
            res = [0, 0, 1, tone]
        else:
            res = [1, 0, 0, tone] if 'lcC' in trial_words_list[i] else [0, 1, 0, tone]  #hit and miss
        res_array = np.append(res_array, [res], axis = 0)
        i+=1
    res_df = pd.DataFrame(res_array, columns = ['hits', 'misses', 'nulls', 'tone'], index = [np.arange(1, len(trial_words_list)+1)])
    # print scores (total hit/miss/null and presentations)
    data = res_df.sum(axis = 0).astype(int)
    scores = data.drop(index='tone', axis=0)
    presentations = scores.sum(axis = 0).astype(int)
    print(scores, "\n\nNumber of Presentations:", presentations)
    print("\nDataframe is stored in result_dataframe! ─=≡Σʕっ•ᴥ•ʔっ")

    return res_df, presentations
    

def plot(res_df, presentations, date_session_df, mouse):
    res_df.reset_index(inplace=True)
    res_df.rename(columns = {'level_0':'real_index'}, inplace=True)
    bins = [np.arange(0, (presentations // 10)*10+1, 10)]
    leftover = presentations%10
    if leftover > 5:  #if leftover bigger than 5, make new bin
        bins.append(leftover)
    else:  #leftover smaller than 5, add to last bin
        bins[0][-1] = (presentations // 10)*10+1+leftover 
    res_df['bins'] = pd.cut(x=res_df['real_index'], bins=bins[0])
    grouped = res_df.groupby('bins')
    # make lists of values for x and y axis for the plots
    bin_list = []
    hit_list_2 = []
    hit_list_8 = []
    null_list_2 = []
    null_list_8 = []
    for index, df in grouped:  #each part of grouped df according to each bin 
        bin_list.append(int(str(index)[1:-1].split(',')[0])/10 +1)
        df_2 = df.query('tone == 2.0')
        df_8 = df.query('tone == 8.0')
        df_list = [df_2, df_8]
        for index, x in enumerate(df_list):
            hitrate = (x['hits'].sum() / (x['hits'].sum() + x['misses'].sum())) * 100
            nullrate = (x['nulls'].sum() / (x['hits'].sum() + x['misses'].sum() + x['nulls'].sum())) * 100
            if index == 0:
                hit_list_2.append(hitrate)
                null_list_2.append(nullrate)
            else:
                hit_list_8.append(hitrate)
                null_list_8.append(nullrate)   
    #make basis for the plots
    plt.style.use("seaborn")
    fig = plt.figure()  #add figure
    gs = fig.add_gridspec(2,2)  #2x2 space graph
    ax1 = fig.add_subplot(gs[0, 0])  #occupy left top
    ax2 = fig.add_subplot(gs[1, 0])  #occupy left bottom
    ax3 = fig.add_subplot(gs[:, 1])  #occupy right 2 spaces
    #plotting out variables             
    ax1.plot(bin_list, hit_list_2, label='2Hz', color='#de7cd9', marker='o', linestyle='dashed', linewidth=2, markersize=7)
    ax1.bar(bin_list, null_list_2, color='#fccff9')
    ax2.plot(bin_list, hit_list_8, label='8Hz', color='#4bd0eb', marker="o", linestyle='dashed', linewidth=2, markersize=7)
    ax2.bar(bin_list, null_list_8, color='#b3e8f2')
    ax3.plot(bin_list, hit_list_2, label='2Hz', color='#de7cd9', marker='o', linestyle='dashed', linewidth=2, markersize=7)
    ax3.plot(bin_list, hit_list_8, label='8Hz', color='#4bd0eb', marker='o', linestyle='dashed', linewidth=2, markersize=7)
    #plot: others
    date = date_session_df['day']
    session = date_session_df['session']
    fig.suptitle(f'Stage 1 Tone Bias Check ({mouse} {date} {session})', fontsize=14)  #main title   
    #subtitles 
    ax1.set_title('2Hz')
    ax2.set_title('8Hz')
    ax3.set_title('2Hz vs. 8Hz')
    #x axis scales
    ax1.set_xticks(bin_list)
    ax2.set_xticks(bin_list)
    ax3.set_xticks(bin_list)
    #x axis scales
    y = [i for i in range(0,101,20)]
    ax1.set_yticks(y)
    ax2.set_yticks(y)
    ax3.set_yticks(y)
    #x/y axis labels
    ax2.set_xlabel("bin #", fontsize=11)
    ax3.set_xlabel("bin #", fontsize=11)
    ax1.set_ylabel('hit rate / null rate', fontsize=11)
    ax2.set_ylabel('hit rate / null rate', fontsize=11)
    ax3.set_ylabel('hit rate', fontsize=11)
    ####
    ax1.legend()
    ax2.legend()
    ax3.legend()
    fig.set_tight_layout(True)  #prevent overlap
            
            
#%%


batch = 'n'

start = time.time()

data_extracting = file_extraction()
organized_files_df = organizing(data_extracting[0], data_extracting[1])

for mouse in organized_files_df:
    for idx in range(len(organized_files_df[mouse])):
        row = organized_files_df[mouse].iloc[idx]
        results = results_df(row)
        plot(results[0], results[1], row, mouse)  #create plot



end = time.time()
execution_time = time.strftime('%H:%M:%S', time.gmtime(end-start))
print(f'This took {execution_time} to run!')



