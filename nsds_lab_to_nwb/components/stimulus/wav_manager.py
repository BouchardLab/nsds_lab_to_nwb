import logging
import os
from scipy.io import wavfile

from pynwb import TimeSeries
from hdmf.backends.hdf5.h5_utils import H5DataIO

from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name
from nsds_lab_to_nwb.utils import get_stim_lib_path

logger = logging.getLogger(__name__)


class WavManager():
    def __init__(self, stim_lib_path, stim_configs):
        self.stim_name = stim_configs['name']
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.stim_configs = stim_configs

    def get_stim_wav(self, starting_time, name='raw_stimulus'):
        # EDIT NOTE: this check is not necessary because get_stim_file handles missing audio_path
        # if self.stim_name in ('wn1', 'baseline'):
        #     return None

        stim_file = self.get_stim_file(self.stim_name, self.stim_lib_path)
        if stim_file is None:
            logger.info(f'Stimulus [{self.stim_name}] has no audio file. ' +
                        'No stimulus will be added to the NWB file.')
            return None

        logger.debug(f'Loading stimulus from: {stim_file}')
        return self._get_stim_wav(stim_file, starting_time, name)

    def _get_stim_wav(self, stim_file, starting_time, name):
        ''' get the raw wav stimulus track '''
        # Read the stimulus wav file
        stim_wav_fs, stim_wav = wavfile.read(stim_file)
        rate = float(stim_wav_fs)

        # Create the stimulus timeseries
        stim_time_series = TimeSeries(name=name,
                                      data=H5DataIO(stim_wav,
                                                    compression=True,
                                                    shuffle=True,
                                                    fletcher32=True),
                                      starting_time=starting_time,
                                      unit='Volts',
                                      rate=rate,
                                      description='Auditory stimulus waveform, aligned to neural recording.')
        return stim_time_series

    @staticmethod
    def get_stim_file(stim_name, stim_path):
        _, stim_info = check_stimulus_name(stim_name)
        if stim_info['audio_path'] is None:
            # when there is no associated audio file (e.g., baseline)
            return None
        return os.path.join(stim_path, stim_info['audio_path'])
