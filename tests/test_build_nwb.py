import os
import numpy as np
import unittest

from nsds_lab_to_nwb.nwb_builder import NWBBuilder
from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager

PWD = os.path.dirname(os.path.abspath(__file__))
USER_HOME = os.path.expanduser("~")


class TestCase_Build_NWB(unittest.TestCase):

    # raw data path
    data_path = '/clusterfs/NSDS_data/hackathon20201201/'

    # new base?
    # data_path_tdt = '/clusterfs/NSDS_data/hackathon20201201/TTankBackup/'

    # output path (this will not be used)
    out_path = os.path.join(USER_HOME, 'Data/nwb_test/')

    def test_build_nwb_case1_old_data(self):
        ''' build NWB but do not write file to disk '''
        animal_name = 'R56'
        block = 'B13'
        # link to metadata files
        block_metadata_path = os.path.join(PWD, f'../yaml/{animal_name}/{animal_name}_{block}.yaml')
        library_path = os.path.join(USER_HOME, 'Src/NSDSLab-NWB-metadata/')
        # collect metadata needed to build the NWB file
        nwb_metadata = MetadataManager(block_metadata_path=block_metadata_path,
                                       library_path=library_path)
        # create a builder for the block
        nwb_builder = NWBBuilder(
                        animal_name=animal_name,
                        block=block,
                        data_path=self.data_path,
                        out_path=self.out_path,
                        nwb_metadata=nwb_metadata
                        )
        # build the NWB file content
        nwb_content = nwb_builder.build()

    def test_build_nwb_case2_new_data_no_stim(self):
        ''' build NWB but do not write file to disk '''
        animal_name = 'RVG02'
        block = 'B09'
        block_name = '{}_{}'.format(animal_name, block)
        # link to metadata files
        block_metadata_path = os.path.join(PWD, f'_data/RVG02/block_data.csv')
        library_path = os.path.join(USER_HOME, 'Src/NSDSLab-NWB-metadata/')
        # collect metadata needed to build the NWB file
        nwb_metadata = MetadataManager(block_name=block_name,
                                       block_metadata_path=block_metadata_path,
                                       library_path=library_path)
        # create a builder for the block
        nwb_builder = NWBBuilder(
                        animal_name=animal_name,
                        block=block,
                        data_path=self.data_path,
                        out_path=self.out_path,
                        nwb_metadata=nwb_metadata
                        )
        # build the NWB file content
        nwb_content = nwb_builder.build(process_stim=False)

if __name__ == '__main__':
    unittest.main()
