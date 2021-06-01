import logging.config
from pynwb.ecephys import ElectricalSeries

from nsds_lab_to_nwb.components.tdt.tdt_reader import TDTReader

logger = logging.getLogger(__name__)


class TdtManager():
    def __init__(self, raw_tdt_path):
        # TDTReader.__init__(self, raw_tdt_path)
        self.tdt_reader = TDTReader(raw_tdt_path)

    def extract(self, device_name, dev_conf, electrode_table_region):
        '''
        extracts TDT data for a single device, and returns an ElectricalSeries.

        Args:
        - device_name: (str) either 'Wave' or 'Poly'
        - dev_conf: (dict) metadata for the device.
                           nwb_builder.metadata['device'][device_name]
        - electrode_table_region: NWB electrode table region for the device
        Returns:
        - e_series: (ElectricalSeries) to be added to the NWB file (returns None if specifed device_name does not exist)
        '''
        logger.info('Extracting for device: {}'.format(device_name))

        stream_list = self.tdt_reader.streams
        if device_name in stream_list:
            result = self.tdt_reader.get_data(device_name)
        else:
            logger.info('- stream {} not found. Available stream list: {}'.format(device_name, stream_list))
            results = None
            # try alternative (device, stream) name pairs
            alternative_device_names = [('ECoG', 'Wave')]
            for dev_name, stream_name in alternative_device_names:
                if device_name == dev_name:
                    result = self.tdt_reader.get_data(stream_name)
                    if result is not None:
                        logger.info('- using alternative stream name: {}'.format(stream_name))
                        break

        if result is None:
            return None

        data, tdt_params = result[0], result[1]
        data = data.T #tranpose to long form matrix
        rate = tdt_params['sample_rate']

        # Create the electrical series
        e_series = ElectricalSeries(name=device_name,
                                    data=data,
                                    electrodes=electrode_table_region,
                                    starting_time=0.,
                                    rate=rate,
                                    )
        return e_series
