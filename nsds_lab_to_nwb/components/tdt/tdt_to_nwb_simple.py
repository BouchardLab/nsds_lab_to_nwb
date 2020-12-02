#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 21:25:55 2020


@author: jhermiz
"""

import tdt
import numpy as np
from pynwb import NWBHDF5IO, NWBFile
from pynwb.ecephys import ElectricalSeries

def tdt_to_nwb(tdt_path, stream, nwbfile):
    '''
    Simple method that dump TDT data from a particular stream to an nwb object for writing (no iterative writing)

    Parameters
    ----------
    tdt_path : string
        Path to TDTTanks
    stream : string
        Name of stream (eg. Poly)
    nwbfile : pynwb.file.NWBFile
        NWBFile object to append TDT to

    Returns
    -------
    nwbfile : pynwb.file.NWBFile
         NWBFile object with TDT added to it as an ElectricalSeries

    '''
    
    tdt_struct = tdt.read_block(tdt_path)
    data = tdt_struct.streams[stream].data.T
    fs = tdt_struct.streams[stream].fs
    channels = tdt_struct.streams[stream].channel
    block_name = tdt_struct.info.blockname
    start_date = tdt_struct.info.start_date
    start_time = tdt_struct.streams[stream].start_time
    
    if nwbfile is None:
        nwbfile = NWBFile('UNK', block_name, start_date,
                      experimenter='UNK',
                      lab='Bouchard Lab',
                      institution='Lawerence Berkeley National Lab',
                      experiment_description='UNK',
                      session_id='UNK')    
    
        device = nwbfile.create_device(name='UNK')
        
        electrode_name = 'UNK'
        description = 'UNK'
        location = 'UNK'
        electrode_group = nwbfile.create_electrode_group(electrode_name,
                                                     description=description,
                                                     location=location,
                                                     device=device)    
    for ch in channels:
        nwbfile.add_electrode(id=int(ch),
                              x=0.0, y=0.0, z=0.0,
                              imp=np.nan,
                              location='UNK', filtering='UNK',
                              group=electrode_group)
    electrode_table_region = nwbfile.create_electrode_table_region([*range(len(channels))], 'UNK')
    
    ephys_ts = ElectricalSeries(stream,
                            data,
                            electrode_table_region,                            
                            starting_time=start_time,
                            rate=fs,
                            resolution=0.001,
                            comments='UNK',
                            description='UNK')
    nwbfile.add_acquisition(ephys_ts)
    return nwbfile

data_directory = '/home/jhermiz/data/hackathon20201201/TTankBackup/R56/R56_B13'    
nwbfile = tdt_to_nwb(data_directory, 'Poly', None)


    
    