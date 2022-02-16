import logging.config
from pynwb import NWBHDF5IO

from process_nwb.resample import store_resample
from process_nwb.wavelet_transform import store_wavelet_transform
from process_nwb import store_linenoise_notch_CAR

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def preprocess_block(nwb_path,
                     acq_name='ECoG',
                     initial_resample_rate=3200.,
                     final_resample_rate=400.,
                     filters='rat',
                     hg_only=True):
    '''
    Performs the following steps:
    1) Resample to frequency and store result,
    2) Remove 60Hz noise and remove and store the CAR, and
    3) Perform and store a wavelet decomposition.

    (Extracted from processed_nwb/scripts/preprocess_folder.py)

    INPUTS:
    -------
    nwb_path: Path to the .nwb file.
              This file will be modified as a result of this function.
    acq_name: Name of the acquisition, either 'ECoG' or 'Poly'.
    initial_resample_rate: Frequency (in Hz) to resample to
                           before performing wavelet transform.
    final_resample_rate: Frequency (in Hz) to resample to
                         after calculating wavelet amplitudes.
    filters: Type of filter bank to use for wavelets.
             Choose from ['rat', 'human', 'changlab'].
    hg_only: Whether to store high gamma bands only. If False, use all filters.

    RETURNS:
    -------
    Returns nothing, but changes the NWB file at nwb_path.
    A ProcessingModule with name 'preprocessing' will be added to the NWB.
    '''
    with NWBHDF5IO(nwb_path, 'a') as io:
        nwbfile = io.read()
        try:
            electrical_series = nwbfile.acquisition[acq_name]
        except KeyError:
            # in case NWB file is in a legacy format
            electrical_series = nwbfile.acquisition['Raw'][acq_name]

        nwbfile.create_processing_module(name='preprocessing',
                                         description='Preprocessing.')

        _, electrical_series_ds = store_resample(electrical_series,
                                                 nwbfile.processing['preprocessing'],
                                                 initial_resample_rate)
        del _

        _, electrical_series_CAR = store_linenoise_notch_CAR(electrical_series_ds,
                                                             nwbfile.processing['preprocessing'])
        del _

        _, electrical_series_wvlt = store_wavelet_transform(electrical_series_CAR,
                                                            nwbfile.processing['preprocessing'],
                                                            filters=filters,
                                                            hg_only=hg_only,
                                                            post_resample_rate=final_resample_rate)
        del _

        io.write(nwbfile)
