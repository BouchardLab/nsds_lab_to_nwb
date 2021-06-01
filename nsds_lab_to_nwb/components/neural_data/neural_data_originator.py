import logging.config
from nsds_lab_to_nwb.components.htk.htk_manager import HtkManager
from nsds_lab_to_nwb.components.tdt.tdt_manager import TdtManager

logger = logging.getLogger(__name__)


class NeuralDataOriginator():
    def __init__(self, dataset, metadata, use_htk=False):
        self.dataset = dataset      # this should have all relavant paths
        self.metadata = metadata    # this should have all relevant metadata

        if use_htk:
            logger.info('Using HTK')
            self.neural_data_manager = HtkManager(self.dataset.raw_htk_path)
        else:
            logger.info('Using TDT')
            self.neural_data_manager = TdtManager(self.dataset.raw_tdt_path)

    def make(self, nwb_content, electrode_table_regions):
        for device_name, dev_conf in self.metadata['device'].items():
            if isinstance(dev_conf, str): # skip other annotations
                continue

            e_series = self.neural_data_manager.extract(device_name, dev_conf,
                                                        electrode_table_regions[device_name])
            if e_series is None:
                logger.info('No e-series extracted. Skipping...')
            else:
                logger.info('Adding extracted e-series to NWB...')
                nwb_content.add_acquisition(e_series)
