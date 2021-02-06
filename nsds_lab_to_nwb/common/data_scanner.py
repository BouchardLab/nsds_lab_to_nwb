import os
from nsds_lab_to_nwb.common.dataset import Dataset


class DataScanner():
    def __init__(self, animal_name, block,
                 data_path: str = '',
                 ):
        self.data_path = data_path
        self.animal_name = animal_name
        self.block = block

    def extract_dataset(self):
        # should be implemented for the specific experiment type
        raise NotImplementedError

    def add_block_subdir(self, path):
        return os.path.join(path, self.animal_name, 
                            self.animal_name + '_' + self.block + '/')


class AuditoryDataScanner(DataScanner):
    def __init__(self, animal_name, block,
                 data_path: str = '',
                 stim_path=None,
                 htk_path=None,
                 tdt_path=None,
                 ):
        DataScanner.__init__(self, animal_name, block, data_path=data_path)

        # detect relevant subdirectories for auditory dataset
        # use default subdirectory name, or override by input
        # ******* TODO: confirm/standardize subdirectory structure *******
        self.stim_path = stim_path or os.path.join(self.data_path, 'Stimulus/')
        self.htk_path = htk_path or os.path.join(self.data_path, 'RatArchive/')
        self.tdt_path = tdt_path or os.path.join(self.data_path, 'TTankBackup/')

    def extract_dataset(self):
        raw_htk_path = self.__get_raw_htk_path()
        raw_tdt_path = self.__get_raw_tdt_path()
        mark_path = self.__find_mark_track()
        return Dataset(data_path=self.data_path, 
                       animal_name=self.animal_name,
                       block=self.block,
                       raw_htk_path=raw_htk_path,
                       raw_tdt_path=raw_tdt_path,
                       mark_path=mark_path,
                       stim_path=self.stim_path,
                       )

    def __find_mark_track(self, mark='mrk11.htk'):
        return os.path.join(self.add_block_subdir(self.htk_path), mark)

    def __get_raw_htk_path(self, raw='RawHTK/'):
        return os.path.join(self.add_block_subdir(self.htk_path), raw)

    def __get_raw_tdt_path(self):
        return self.add_block_subdir(self.tdt_path)


class BehaviorDataScanner(DataScanner):
    def __init__(self, animal_name, block,
                 data_path: str = '',
                 video_path=None,
                 ):
        DataScanner.__init__(self, animal_name, block, data_path=data_path)
                            
        # TODO: collect and pass relevant subdirectories. maybe video_path?
        self.video_path = video_path or os.path.join(self.data_path, 'Video/') # <<<< replace accordingly

    def extract_dataset(self):
        # TODO for behavior (reaching) data
        raise NotImplementedError
