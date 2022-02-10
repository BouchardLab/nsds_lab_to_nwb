import logging
import numpy as np

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class BaseTokenizer():
    """ Base Tokenizer class for auditory stimulus data
    """
    def __init__(self, block_name, stim_configs):
        self.block_name = block_name
        self.stim_configs = stim_configs

        self.tokenizer_type = 'BaseTokenizer'
        self.custom_trial_columns = None

    def tokenize(self, mark_onsets, mark_time_series, stim_vals):
        stim_onsets = self.get_stim_onsets(mark_onsets, mark_time_series)
        self._validate_num_stim_onsets(stim_vals, stim_onsets)
        rec_end_time = mark_time_series.num_samples / mark_time_series.rate
        trial_list = self._tokenize(stim_vals, stim_onsets,
                                    stim_dur=self.stim_configs['duration'],
                                    bl_start=self.stim_configs['baseline_start'],
                                    bl_end=self.stim_configs['baseline_end'],
                                    rec_end_time=rec_end_time)
        return trial_list

    def _tokenize(self, stim_vals, stim_onsets,
                  *, stim_dur, bl_start, bl_end, rec_end_time):
        raise NotImplementedError

    def get_stim_onsets(self, mark_onsets, mark_time_series):
        """
        if mark_onsets is not None:
            # loaded directly from TDT object
            logger.info('Using stimulus onsets directly loaded from TDT')
            return mark_onsets
            """

        logger.info('Detecting stimulus onsets by thresholding the mark track')
        mark_fs = mark_time_series.rate
        mark_offset = self.stim_configs['mark_offset']
        mark_threshold = self._get_mark_threshold()
        stim_onsets_idx = self._get_stim_onsets(mark_time_series, mark_threshold)
        stim_onsets = (stim_onsets_idx / mark_fs) + mark_offset
        return stim_onsets

    def _get_stim_onsets(self, mark_time_series, mark_threshold):
        mark_data = mark_time_series.data[:]
        thresh_crossings = np.diff((mark_data > mark_threshold).astype('int'),
                                   axis=0)

        # adding +1 because diff gets rid of the 1st datapoint
        stim_onsets_idx = np.where(thresh_crossings > 0.5)[0] + 1
        logger.debug(f'found {len(stim_onsets_idx)} onsets')
        return stim_onsets_idx

    def _get_mark_threshold(self):
        # NOTE: this is only used when TDT-loaded mark onsets are not available.
        # see issue #102 for more discussion on mark thresholds.
        mark_threshold = self.stim_configs['mark_threshold']
        logger.debug(f'using mark_threshold={mark_threshold} from metadata input')
        return mark_threshold

    def _validate_num_stim_onsets(self, stim_vals, stim_onsets):
        ''' Validate that the number of identified stim onsets
        is equal to the number of stim parameterizations in stim_vals.
        '''
        num_onsets = len(stim_onsets)
        num_expected_trials = len(stim_vals)
        mismatch_msg = (
            f"{self.tokenizer_type}: "
            + "Incorrect number of stimulus onsets found "
            + f"in block {self.block_name}. "
            + f"Expected {num_expected_trials}, found {num_onsets}.")

        if num_onsets != num_expected_trials:
            raise ValueError(mismatch_msg)
