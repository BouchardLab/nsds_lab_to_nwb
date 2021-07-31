#!/user/bin/env python
import logging.config
import argparse
from importlib.resources import path

import nsds_lab_to_nwb
from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path,
                                   get_stim_lib_path)
from nsds_lab_to_nwb.nwb_builder import NWBBuilder


with path(nsds_lab_to_nwb, 'logging.conf') as fname:
    logging.config.fileConfig(fname, disable_existing_loggers=False)

parser = argparse.ArgumentParser(description='Convert to a NWB file.')
parser.add_argument('save_path', type=str, help='Path to save the NWB file.')
parser.add_argument('block_folder', type=str, help='<animal>_<block> block specification.')
parser.add_argument('--block_metadata_path', '-e', type=str, default=None,
                    help='Path to block metadata file.')
parser.add_argument('--data_path', '-d', type=str, default=None,
                    help='Path to the top level data folder.')
parser.add_argument('--metadata_lib_path', '-m', type=str, default=None,
                    help='Path to the metadata library repo.')
parser.add_argument('--stim_lib_path', '-s', type=str, default=None,
                    help='Path to the stimulus library.')
parser.add_argument('--use_htk', '-k', action='store_true',
                    help='Use data from HTK rather than TDT files.')

args = parser.parse_args()
save_path = args.save_path
block_folder = args.block_folder
block_metadata_path = args.block_metadata_path
data_path = get_data_path(args.data_path)
metadata_lib_path = get_metadata_lib_path(args.metadata_lib_path)
stim_lib_path = get_stim_lib_path(args.stim_lib_path)
use_htk = args.use_htk

# --- build NWB file for the specified block ---
# NOTE: metadata collection is now done in NWBBuilder.__init__()
# create a builder for the block
nwb_builder = NWBBuilder(
    data_path=data_path,
    block_folder=block_folder,
    save_path=save_path,
    block_metadata_path=block_metadata_path,
    metadata_lib_path=metadata_lib_path,
    stim_lib_path=stim_lib_path,
    use_htk=use_htk)

# build the NWB file content
nwb_content = nwb_builder.build()

# write to file
nwb_builder.write(nwb_content)
