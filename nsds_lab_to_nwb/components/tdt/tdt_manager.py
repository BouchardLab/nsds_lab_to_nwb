from nsds_lab_to_nwb.components.tdt.tdt_reader import TDTReader
from pynwb.ecephys import ElectricalSeries

class TdtManager(TDTReader):    
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
        result = self.get_data(device_name)
        if result is None:
            return None
        else:
            data, tdt_params = result[0], result[1]
        data = data.T #tranpose to long form matrix
        rate = tdt_params['sample_rate']

        # Create the electrical series
        e_series = ElectricalSeries(name=device_name,
                                    data=data,
                                    electrodes=electrode_table_region,
                                    starting_time=0.,
                                    rate=rate,
                                    # **add_other_fields_as_necessary
                                    )
        return e_series
