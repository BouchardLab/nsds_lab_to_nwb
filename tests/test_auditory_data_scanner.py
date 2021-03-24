import os
import numpy as np
import unittest

from nsds_lab_to_nwb.common.auditory_data_scanner import AuditoryDataScanner


class TestCase_DataScanning(unittest.TestCase):

    # raw data path
    data_path = '/clusterfs/NSDS_data/hackathon20201201/'

    # new base?
    data_path_tdt = '/clusterfs/NSDS_data/hackathon20201201/TTankBackup/'

    def test_auditory_data_scanner_case1_old_data(self):
        ''' scan data_path and identify relevant subdirectories '''
        animal_name = 'R56'
        block = 'B13'
        data_scanner = AuditoryDataScanner(
            animal_name, block, data_path=self.data_path)
        # TODO: if there is any error, it should be raised through data_scanner
        # for now no validation is done
        dataset = data_scanner.extract_dataset()

    def test_auditory_data_scanner_case2_new_data(self):
        ''' scan data_path and identify relevant subdirectories '''
        animal_name = 'RVG02'
        block = 'B09'
        data_scanner = AuditoryDataScanner(
            animal_name, block, data_path=self.data_path_tdt)
        # TODO: if there is any error, it should be raised through data_scanner
        # for now no validation is done
        dataset = data_scanner.extract_dataset()

if __name__ == '__main__':
    unittest.main()
