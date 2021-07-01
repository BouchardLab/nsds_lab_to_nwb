import os
from scipy.io import wavfile

from pynwb import TimeSeries

from nsds_lab_to_nwb.components.stimulus.stim_value_extractor import StimValueExtractor
from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
from nsds_lab_to_nwb.utils import get_stim_lib_path


class WavManager():
    def __init__(self, stim_lib_path, stim_configs):
        self.stim_name = stim_configs['name']
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.stim_configs = stim_configs
        self._load_stim_values()

    def get_stim_wav(self, starting_time, name='raw_stimulus'):
        if self.stim_name == 'wn1':
            return None
        return self._get_stim_wav(self.get_stim_file(self.stim_name, self.stim_lib_path),
                                  starting_time, name=name)

    def _get_stim_wav(self, stim_file, starting_time, name='raw_stimulus'):
        ''' get the raw wav stimulus track '''
        # Read the stimulus wav file
        stim_wav_fs, stim_wav = wavfile.read(stim_file)

        # Create the stimulus timeseries
        rate = float(stim_wav_fs)
        stim_time_series = TimeSeries(name=name,
                                      data=stim_wav,
                                      starting_time=starting_time,
                                      unit='Volts',
                                      rate=rate,
                                      description='The neural recording aligned stimulus track.')
        return stim_time_series

    @staticmethod
    def get_stim_file(stim_name, stim_path):
        _, stim_info = check_stimulus_name(stim_name)
        return os.path.join(stim_path, stim_info['audio_path'])

    def _load_stim_values(self):
        '''load stim_values from .mat or .csv files,
        or generate using original script (mars/configs/block_directory.py)
        '''
        sve = StimValueExtractor(self.stim_configs, self.stim_lib_path)
        self.stim_configs['stim_values'] = sve.extract()
