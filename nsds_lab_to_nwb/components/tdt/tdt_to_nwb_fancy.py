#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 14:48:43 2020

@author: jhermiz
"""

### This is supposed to do iterative writing to an NWB, but doesn't work
### I get a stupid broadcast error, not sure how to solve?!? Come back to!


import tdt
from datetime import datetime
from dateutil.tz import tzlocal
from pynwb import NWBFile, TimeSeries
from pynwb import NWBHDF5IO
import numpy as np
from hdmf.data_utils import DataChunkIterator

BUFFER_SIZE = 2

def write_nwb(filename, data): #for debugging
    """
    Simple helper function to write an NWBFile with a single timeseries containing data
    :param filename: String with the name of the output file
    :param data: The data of the timeseries
    """

    # Create a test NWBfile
    start_time = datetime(2017, 4, 3, 11, tzinfo=tzlocal())
    create_date = datetime(2017, 4, 15, 12, tzinfo=tzlocal())
    nwbfile = NWBFile('demonstrate NWBFile basics',
                      'NWB123',
                      start_time,
                      file_create_date=create_date)
    
    # Create our time series
    test_ts = TimeSeries(name='synthetic_timeseries',
                         data=data,                     # <---------
                         unit='SIunit',
                         rate=1.0,
                         starting_time=0.0)
    nwbfile.add_acquisition(test_ts)
    
    # Write the data to file
    io = NWBHDF5IO(filename, 'w')
    try:
        io.write(nwbfile)
    except:
        io.close()
    io.close()

def iter_tdt_channels(tdt_path, stream, header, num_channels):
    #this is inefficient because it loads all streams. As far as I can tell,
    #there's no way to select streams to load
    #TODO: save other streams to NWB since they are loaded anyway
    for ch in range(num_channels):
        tdt_ch = ch + 1
        tdt_struct = tdt.read_block(tdt_path, 
                                    channel=tdt_ch, 
                                    #headers=header, 
                                    evtype=['streams'])
        ch_data = tdt_struct.streams[stream].data
        print(ch_data.shape)
        yield ch_data
    return

def tdt_to_nwb(tdt_path, stream):    
    header = tdt.read_block(tdt_path, headers=1)
    num_channels = len(header.stores[stream].chan)
    datashape = (35653632, num_channels)    
    data = DataChunkIterator(data=iter_tdt_channels(tdt_path, stream, header, num_channels),
                             maxshape=datashape,
                             buffer_size=BUFFER_SIZE) 
    write_nwb('test.nwb', data)
    
    

data_directory = '/home/jhermiz/data/hackathon20201201/TTankBackup/R56/R56_B10'    
tdt_to_nwb(data_directory, 'Poly')
#1114176
#35653632

#%%

# def test_iter_tdt_channels(tdt_path, stream, header, num_channels):
#     #this is inefficient because it loads all streams. As far as I can tell,
#     #there's no way to select streams to load
#     #TODO: save other streams to NWB since they are loaded anyway
#     for ch in range(num_channels):
#         tdt_ch = ch + 1
#         tdt_struct = tdt.read_block(tdt_path, 
#                                     channel=tdt_ch, 
#                                     #headers=header, 
#                                     evtype=['streams'])
#         ch_data = tdt_struct.streams[stream].data
#         print(ch_data.shape)        
#     return

# tdt_path = data_directory
# stream = 'Poly'
# header = tdt.read_block(tdt_path, headers=1)
# num_channels = len(header.stores[stream].chan)
# datashape = (35653632, num_channels)    
# test_iter_tdt_channels(tdt_path, stream, header, num_channels)

