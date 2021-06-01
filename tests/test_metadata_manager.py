import os
import numpy as np
import unittest

from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager

PWD = os.path.dirname(os.path.abspath(__file__))
USER_HOME = os.path.expanduser("~")


class TestCase_MetadataManager(unittest.TestCase):

    # raw data path
    data_path = '/clusterfs/NSDS_data/hackathon20201201/'

    # new base?
    data_path_tdt = '/clusterfs/NSDS_data/hackathon20201201/TTankBackup/'


    def test_metadata_manager_case1_old_data(self):
        ''' detect/collect metadata needed to build the NWB file '''
        animal_name = 'R56'
        block = 'B13'
        block_metadata_path = os.path.join(PWD, f'../yaml/{animal_name}/{animal_name}_{block}.yaml')
        library_path = os.path.join(USER_HOME, 'Src/NSDSLab-NWB-metadata/')
        nwb_metadata = MetadataManager(block_metadata_path=block_metadata_path,
                                       library_path=library_path)
        nwb_metadata.extract_metadata()

    def test_metadata_manager_case2_new_data(self):
        ''' detect/collect metadata needed to build the NWB file '''
        animal_name = 'RVG02'
        block = 'B09'
        block_name = '{}_{}'.format(animal_name, block)
        block_metadata_path = os.path.join(PWD,
            f'_data/RVG02/block_data.csv')
        library_path = os.path.join(USER_HOME, 'Src/NSDSLab-NWB-metadata/')
        nwb_metadata = MetadataManager(block_name=block_name,
                                       block_metadata_path=block_metadata_path,
                                       library_path=library_path)
        nwb_metadata.extract_metadata()

if __name__ == '__main__':
    unittest.main()
