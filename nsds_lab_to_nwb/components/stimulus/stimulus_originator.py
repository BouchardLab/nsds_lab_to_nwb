import logging

from nsds_lab_to_nwb.components.stimulus.mark_manager import MarkManager
from nsds_lab_to_nwb.components.stimulus.stim_value_extractor import StimValueExtractor
from nsds_lab_to_nwb.components.stimulus.trials_manager import TrialsManager
from nsds_lab_to_nwb.components.stimulus.wav_manager import WavManager
from nsds_lab_to_nwb.utils import get_stim_lib_path

logger = logging.getLogger(__name__)


class StimulusOriginator():
    def __init__(self, dataset, metadata):
        self.dataset = dataset
        self.metadata = metadata
        self.stim_lib_path = get_stim_lib_path(self.dataset.stim_lib_path)
        self.stim_configs = self.metadata['stimulus']

        self.stim_vals = StimValueExtractor(self.stim_configs,
                                            self.stim_lib_path).extract()

        self.mark_manager = MarkManager(self.dataset)
        self.trials_manager = TrialsManager(self.metadata['block_name'],
                                            self.stim_configs)

        self.wav_manager = WavManager(self.stim_lib_path,
                                      self.stim_configs)

        # names for mark and stimulus time series objects
        self.mark_obj_name = 'stim_onset_marks'  # 'recorded_mark' (previous name)
        self.stim_wav_obj_name = 'stim_waveform'  # 'raw_stimulus' (previous name)

    def make(self, nwb_content, tdt_reader=None):
        stim_name = self.stim_configs['name']
        stim_type = self.stim_configs['type']  # either 'discrete' or 'continuous'
        logger.info(f'Stimulus name: {stim_name} (type: {stim_type})')

        # add mark track
        logger.info('Adding marks...')
        mark_starting_time = 0.0    # see issue #88 for discussion
        mark_time_series, mark_onsets = self.mark_manager.get_mark_track(starting_time=mark_starting_time,
                                                                         name=self.mark_obj_name,
                                                                         tdt_reader=tdt_reader)
        nwb_content.add_stimulus(mark_time_series)

        # tokenize into trials, once mark track has been added to nwb_content
        logger.info('Tokenizing into trials...')
        self.trials_manager.add_trials(nwb_content, mark_onsets, self.stim_vals,
                                       mark_obj_name=self.mark_obj_name)

        # add stimulus WAV data
        logger.info('Adding stimulus waveform...')
        stim_starting_time = self._get_stim_starting_time(nwb_content)
        stim_wav_time_series = self.wav_manager.get_stim_wav(starting_time=stim_starting_time,
                                                             name=self.stim_wav_obj_name)
        if stim_wav_time_series is not None:
            nwb_content.add_stimulus(stim_wav_time_series)

    def _get_stim_starting_time(self, nwb_content):
        try:
            time_table = nwb_content.trials.to_dataframe().query('sb == "s"')['start_time']
            first_recorded_mark = time_table.values[0]
        except IndexError:
            # there may be no 's' trial if it was a 'baseline' stimulus block
            first_recorded_mark = 0.0    # see issue #88 for discussion

        # starting time for the stimulus TimeSeries
        stim_starting_time = (first_recorded_mark
                              - self.stim_configs['mark_offset']  # adjust for mark offset
                              - self.stim_configs['first_mark'])  # time between stimulus DVD start and the first mark
        return stim_starting_time
