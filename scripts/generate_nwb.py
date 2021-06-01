import logging.config
import os

from nsds_lab_to_nwb.nwb_builder import NWBBuilder
from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager

PWD = os.path.dirname(os.path.abspath(__file__))
USER_HOME = os.path.expanduser("~")

logging.config.fileConfig(fname=str(PWD) + '/../nsds_lab_to_nwb/logging.conf', disable_existing_loggers=False)


# --- user input and metadata for an experiment block ---

animal_name = 'R56'
# block = 'B10'
block = 'B13'

# raw data path
data_path = '/clusterfs/NSDS_data/hackathon20201201/'

# output path
# out_path = os.path.join(USER_HOME, 'Data/nwb_test/')
out_path = '/clusterfs/NSDS_data/jhbak/nwb/'

# link to metadata files
block_metadata_path = os.path.join(PWD, f'../yaml/{animal_name}/{animal_name}_{block}.yaml')
metadata_lib_path = os.path.join(USER_HOME, 'Src/NSDSLab-NWB-metadata/')
stim_lib_path = None # not used
# stim_lib_path = os.path.join(metadata_lib_path, 'auditory',
#         'configs_legacy/mars_configs/') # <<<< should move to a stable location


# --- build NWB file for the specified block ---

# NOTE: metadata collection is now done in NWBBuilder.__init__()

# create a builder for the block
nwb_builder = NWBBuilder(
                animal_name=animal_name,
                block=block,
                data_path=data_path,
                out_path=out_path,
                block_metadata_path=block_metadata_path,
                metadata_lib_path=metadata_lib_path,
                stim_lib_path=stim_lib_path,
                #use_htk=True # for testing HTK pipeline (default is False)
                )

# build the NWB file content
nwb_content = nwb_builder.build()

# write to file
nwb_builder.write(nwb_content)
