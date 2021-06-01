from pynwb.ecephys import ElectricalSeries

from nsds_lab_to_nwb.components.htk.readers.instrument import EPhysInstrumentData


class HtkManager():
    def __init__(self, raw_path):
        self.raw_path = raw_path

    def extract(self, device_name, dev_conf, electrode_table_region):
        ''' adapted from mars.HTKNWB.add_raw_htk
        now manages one device at a time
        '''
        # Create the instrument reader
        device_reader = EPhysInstrumentData(
                        htkdir=self.raw_path,
                        prefix=dev_conf['prefix'],
                        postfix=dev_conf['ch_ids'],
                        device_name=dev_conf['device_type'],
                        read_on_create=False)

        # Read the raw data with the device_reader
        device_reader.read_data(create_iterator=True, time_axis_first=True, has_bands=False)

        # Create the electrical series
        e_series = ElectricalSeries(name=device_name, #name
                                    data=device_reader.data, #data
                                    electrodes=electrode_table_region, #electrode table region
                                    starting_time=0.0,
                                    rate=dev_conf['sampling_rate'])
        return e_series
