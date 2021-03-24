import tdt
import numpy as np
import warnings
from pynwb.ecephys import ElectricalSeries
from hdmf.data_utils import DataChunkIterator

BUFFER_SIZE = 32  # Buffer these many channels into a chunk


class TdtManager():
    def __init__(self, tdt_path, verbose=False):
        self.tdt_path = tdt_path
        self.verbose = verbose
        self.tdt_object = self.get_tdt_object()
        self.tdt_streams = self.get_stream_list()

        if self.verbose:
            print('Available streams:')
            print(self.tdt_streams)

    def get_tdt_object(self):
        '''
        gets TDT meta data object

        Returns:
        - tdt_object: (struct) TDT meta data object
        '''
        tdt_object = tdt.read_block(self.tdt_path, headers=1)
        return tdt_object

    def get_stream_list(self):
        '''
        gets TDT meta data object

        Returns:
        - streams: (list) list of TDT stream names in file
        '''
        x = list(self.tdt_object['stores'].__dict__.items())
        streams = [e[0] for e in x]
        return streams

    def extract_tdt(self, device_name, dev_conf, electrode_table_region):
        '''
        extracts TDT data for a single device, and returns an ElectricalSeries.

        Args:
        - device_name: (str) either 'ECoG' or 'Poly'
        - dev_conf: (dict) metadata for the device.
                           nwb_builder.metadata['device'][device_name]
        - electrode_table_region: NWB electrode table region for the device
        Returns:
        - e_series: (ElectricalSeries) to be added to the NWB file
        '''
        if device_name not in self.tdt_streams:
            error_message = 'Device or stream not found: {}. Available streams: '.format(device_name)
            for stream in self.tdt_streams:
                error_message += stream + ', '
            # raise AttributeError(error_message)
            # -- instead just warn and skip this probe;
            # -- None will be detected as an error flag in tdt_originator
            warnings.warn(error_message)
            return None

        data, tdt_params = self.__extract_stream_data(device_name, dev_conf)
        rate = tdt_params['sample_rate']
        start_time = tdt_params['start_time']

        # Create the electrical series
        e_series = ElectricalSeries(name=device_name,
                                    data=data,
                                    electrodes=electrode_table_region,
                                    starting_time=start_time,
                                    rate=rate,
                                    # **add_other_fields_as_necessary
                                    )
        return e_series

    def __extract_stream_data(self, device_name, dev_conf):
        '''
        extracts TDT stream

        Args:
        - device_name: (str) stream name (eg. 'ECoG' or 'Poly')
        - dev_conf: (dict) metadata for the device.
                           nwb_builder.metadata['device'][device_name]

        Returns:
        - data: (numpy array) [samples] by [channels]
        - parameters (dict) includes stream meta data
        '''
        tdt_struct = tdt.read_block(self.tdt_path, store=device_name)
        stream = tdt_struct.streams[device_name]
        data = stream.data.T
        parameters = {'start_time': stream.start_time,
                      'sample_rate': stream.fs}
        return data, parameters

    ### Iterative now fails bc it results in a eseries of 1 and 0s ###
    ### Not sure what changed from last time ###
    # def __iter_tdt_channels(self, tdt_path, stream, header, num_channels):
    #     '''
    #     generator function for DataIterator, yields one channel each iteration

    #     Args:
    #     - tdt_path : (str) path for tdt directory
    #     - stream : (str) data stream name such as'ECoG' or 'Poly'
    #     - header : (struct) returned by tdt.read_block has recording meta-data
    #     - num_channels : (int) number of channels in the data stream

    #     Yields:
    #     - ch_data : (iterator object) iterator object for one channel
    #     '''
    #     # This is inefficient because it loads all streams. I believe there's
    #     # No way to select streams to load. Possible future improvement
    #     for ch in range(num_channels):
    #         tdt_ch = ch + 1
    #         tdt_struct = tdt.read_block(tdt_path,
    #                                     channel=tdt_ch,
    #                                     headers=header,
    #                                     evtype=['streams'])
    #         ch_data = tdt_struct.streams[stream].data

    #         # Transpose data because that's what NWB expects
    #         ch_data = np.reshape(1, -1)
    #         yield ch_data
    #     return

    # def __extract_stream_data(self, device_name, dev_conf):
    #     '''
    #     generator function for DataIterator, yields one channel each iteration

    #     Args:
    #     - device_name : (str) data stream name such as'ECoG' or 'Poly'
    #     - dev_conf: (dict) metadata for the device.
    #                        nwb_builder.metadata['device'][device_name]

    #     Returns: data, tdt_parms (tuple):
    #     - data : (DataChunkIterator) tdt data as an iterator object
    #     - tdt_params: (dict) tdt recording meta-data
    #     '''
    #     tdt_path = self.tdt_path
    #     header = self.tdt_object
    #     tdt_tmp = tdt.read_block(tdt_path, channel=1)

    #     num_channels = len(np.unique(header.stores[device_name].chan))
    #     num_samples = len(tdt_tmp.streams[device_name].data) // num_channels
    #     # Iteratively write one channel at a time
    #     stream_data = DataChunkIterator(data=self.__iter_tdt_channels(
    #         tdt_path,
    #         device_name,
    #         header,
    #         num_channels),
    #         maxshape=(num_samples, num_channels),
    #         buffer_size=BUFFER_SIZE)
    #     stream_parameters = {}
    #     stream_parameters['sample_rate'] = header.stores[device_name].fs
    #     stream_parameters['num_channels'] = num_channels
    #     stream_parameters['num_samples'] = num_samples
    #     return stream_data, stream_parameters
