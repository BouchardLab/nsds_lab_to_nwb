import logging.config
from pynwb.ecephys import ElectricalSeries

from nsds_lab_to_nwb.tools.htk.htk_reader import HTKReader
from nsds_lab_to_nwb.tools.tdt.tdt_reader import TDTReader
from process_nwb.resample import resample
from hdmf.backends.hdf5.h5_utils import H5DataIO

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NeuralDataOriginator():
    def __init__(self, dataset, metadata, resample_flag=True):
        self.dataset = dataset      # this should have all relavant paths
        self.metadata = metadata    # this should have all relevant metadata
        self.resample_flag = resample_flag
        self.hardware_rate = None
        self.resample_rate = None

        if hasattr(self.dataset, 'htk_mark_path'):
            logger.info('Using HTK')
            self.neural_data_reader = HTKReader(self.dataset.htk_path)
            self.tdt_reader = None
        else:
            logger.info('Using TDT')
            self.neural_data_reader = TDTReader(self.dataset.tdt_path)
            self.tdt_reader = self.neural_data_reader

    def make(self, nwb_content, electrode_table_regions):
        for device_name, dev_conf in self.metadata['device'].items():
            if isinstance(dev_conf, str): # skip other annotations
                continue

            logger.info(f'Extracting {device_name} data...')
            data, metadata = self.neural_data_reader.get_data(stream=device_name, dev_conf=dev_conf)
            if data is None:
                logger.info(f'No data available for {device_name}. Skipping...')
            else:
                # resample data
                self.hardware_rate = metadata['sample_rate']
                if self.resample_flag:
                    logger.info('Resampling to the nearest kHz...')
                    data = self.resample(data)
                    logger.info('Resampling successful.')

                # make description
                description = self._get_description(device_name)

                # make comments (mention bad channels)
                comments = self._get_comments(dev_conf)

                electrode_table_region = electrode_table_regions[device_name]
                e_series = ElectricalSeries(name=device_name,
                                            data=H5DataIO(data,
                                                          compression=True,
                                                          shuffle=True,
                                                          fletcher32=True),
                                            electrodes=electrode_table_region,
                                            starting_time=0.,
                                            rate=self._get_rate(),
                                            description=description,
                                            comments=comments,
                                            conversion=dev_conf.get('conversion', 1.),
                                            resolution=dev_conf.get('resolution', 1.)
                                            )
                logger.info(f'Adding {device_name} data to NWB...')
                logger.debug(f' - Description: {description}')
                logger.debug(f' - Comments: {comments}')
                nwb_content.add_acquisition(e_series)
        return self.tdt_reader

    def resample(self, data):
        # only resample if rate is not at nearest kHz
        rate = self.hardware_rate
        if (rate / 1000 % 1) > 0:
            new_freq = (rate // 1000) * 1000
            logger.info(f' - resampling from {rate} Hz to {new_freq} Hz')
            new_data = resample(data, new_freq, rate)
            self.resample_rate = new_freq
            return new_data
        else:
            # no need to resample, already at nearest kHz
            logger.info(' - already at integer kHz; no need to resample')
            self.resample_flag = False
            return data

    def _get_description(self, device_name):
        description = self.metadata['experiment_description']
        description += '. Recordings from {0:s} sampled at {1:f} Hz.'.format(device_name,
                                                                             self.hardware_rate)
        if self.resample_flag:
            description += ' Then resampled down to {0:d} Hz'.format(int(self.resample_rate))
        return description

    def _get_comments(self, dev_conf):
        if 'bad_chs' not in dev_conf:
            return ''

        ch_map = dev_conf['ch_map']
        comments = 'bad_channels=['
        comments += (", ".join([str(ch_map[i]['electrode_id'])  # re-map channels
                                for i in dev_conf['bad_chs']])).rstrip(', ')
        comments += "]"
        return comments

    def _get_rate(self):
        if self.resample_rate is None:
            rate = self.hardware_rate
        else:
            rate = self.resample_rate
        return rate * 1.0
