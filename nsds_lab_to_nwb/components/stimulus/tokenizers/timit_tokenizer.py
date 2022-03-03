from nsds_lab_to_nwb.components.stimulus.tokenizers.base_tokenizer import BaseTokenizer


class TIMITTokenizer(BaseTokenizer):
    """
    Tokenize into TIMIT stimulus trials.
    """
    def __init__(self, block_name, stim_configs):
        BaseTokenizer.__init__(self, block_name, stim_configs)
        self.tokenizer_type = 'TIMITTokenizer'

        # list of ('column_name', 'column_description')
        self.custom_trial_columns = [('sb', 'Stimulus (s) or baseline (b) period'),
                                     ('sample_filename', 'Sample Filename')]

    def _load_stim_parameters(self):
        stim_params_path = self.stim_configs['stim_params_path']
        stim_vals = timit_stimulus_values(stim_params_path)
        return stim_vals

    def _tokenize(self, stim_vals, stim_onsets,
                  *, audio_start_time, audio_end_time, rec_end_time):
        # bl_gap: gap between baseline and stimulus periods
        # (use the same value for both the pre- and post-stim baselines)
        bl_gap = self.stim_configs['baseline_start']
        if self.stim_configs.get('baseline_end', None) is not None:
            raise ValueError('baseline_end is assumed to have null/None value, '
                             'meaning that baselines extend to the ends of recoding')

        trial_list = []

        # period before the first stimulus starts
        stop_time = stim_onsets[0] - bl_gap
        if stop_time > 0.0:
            trial_list.append(dict(start_time=0.0,
                                   stop_time=stop_time,
                                   sb='b',
                                   sample_filename='none'))

        for i, onset in enumerate(stim_onsets):
            filename = str(stim_vals[i])
            try:
                stop_time = stim_onsets[i + 1]
            except IndexError:
                stop_time = audio_end_time
            trial_list.append(dict(start_time=onset,
                                   stop_time=stop_time,
                                   sb='s',
                                   sample_filename=filename))

        # period after the end of last stim trial until recording stops
        start_time = audio_end_time + bl_gap
        if start_time < rec_end_time:
            trial_list.append(dict(start_time=start_time,
                                   stop_time=rec_end_time,
                                   sb='b',
                                   sample_filename='none'))

        return trial_list


def timit_stimulus_values(file_path):
    """adapted from mars.configs.block_directory

    Parameters
    -----------
    file_path : full path to a .txt file that contains a list of filenames

    Returns
    --------
    stim_vals: list of str
        each item is a .wav file name in TIMIT.
    """
    # expecting a text file, one .wav filename string per row
    with open(file_path) as f:
        lines = f.readlines()
    stim_vals = [line.rstrip(' \n') for line in lines]
    return stim_vals
