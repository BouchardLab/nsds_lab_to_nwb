import numpy as np

from nsds_lab_to_nwb.components.stimulus.tokenizers.stimulus_tokenizer import StimulusTokenizer


class TIMITTokenizer(StimulusTokenizer):
    """
    Tokenize TIMIT stimulus data

    Original version author: Max Dougherty <maxdougherty@lbl.gov>
    As part of MARS
    """
    def __init__(self, block_name, stim_configs):
        StimulusTokenizer.__init__(self, block_name, stim_configs)

    def tokenize(self, nwb_content, mark_name='recorded_mark'):
        """
        """
        if self.__already_tokenized(nwb_content):
            print('Block has already been tokenized')
            return

        stim_onsets = self.__get_stim_onsets(nwb_content, mark_name)
        stim_vals = self.stim_configs['stim_values']
        stim_dur = self.stim_configs['duration']
        bl_start = self.stim_configs['baseline_start']
        bl_end = self.stim_configs['baseline_end']

        nwb_content.add_trial_column('sb', 'Stimulus (s) or baseline (b) period')
        nwb_content.add_trial_column('sample_filename', 'Sample Filename')

        # Add the pre-stimulus period to baseline
        nwb_content.add_trial(start_time=0.0, stop_time=stim_onsets[0]-stim_dur, sb='b',sample_filename=stim_vals[0])

        # TODO: Assert that the # of stim vals is equal to the number of found onsets
        assert len(stim_onsets)==len(stim_vals), (
                    "Incorrect number of stimulus onsets found."
                    + " Expected {:d}, found {:d}.".format(len(stim_vals), len(stim_onsets))
                    + " Perhaps you are not using the correct tokenizer?"
                    )
        for i, onset in enumerate(stim_onsets):
            filename = str(stim_vals[i])
            nwb_content.add_trial(start_time=onset, stop_time=onset+stim_dur, sb='s',sample_filename=filename)
            #nwb_content.add_trial(start_time=onset+bl_start, stop_time=onset+bl_end, sb='b',frq=frq,amp=amp)

        # Add the period after the last stimulus to  baseline
        rec_end_time = self._get_end_time(nwb_content, mark_name)
        nwb_content.add_trial(start_time=stim_onsets[-1]+bl_end, stop_time=rec_end_time, sb='b', sample_filename=stim_vals[-1])

    def __already_tokenized(self, nwb_content):
        return (nwb_content.trials and
                'sb' in nwb_content.trials.colnames and
                'frq' in nwb_content.trials.colnames and
                'amp' in nwb_content.trials.colnames)

    def __get_stim_onsets(self, nwb_content, mark_name):
        mark_dset = self.read_mark(nwb_content, mark_name)
        mark_fs = mark_dset.rate
        mark_offset = self.stim_configs['mark_offset']
        stim_dur = self.stim_configs['duration']

        mark_trk, mark_threshold = self.__get_mark_threshold(mark_dset)
        thresh_crossings = np.diff( (mark_trk > mark_threshold).astype('int'), axis=0)
        stim_onsets = np.where(thresh_crossings > 0.5)[0] + 1
        return (stim_onsets / mark_fs) + mark_offset

    def __get_mark_threshold(self, mark_dset):
        return mark_dset.data[:], self.stim_configs['mark_threshold']
