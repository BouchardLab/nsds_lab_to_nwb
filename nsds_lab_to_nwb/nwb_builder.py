import logging.config
import os
from os.path import join, exists
import uuid
from datetime import datetime
import pytz

from pynwb import NWBHDF5IO, NWBFile
from pynwb.file import Subject

from nsds_lab_to_nwb.common.auditory_data_scanner import AuditoryDataScanner
from nsds_lab_to_nwb.common.behavior_data_scanner import BehaviorDataScanner
from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager

from nsds_lab_to_nwb.components.device.device_originator import DeviceOriginator
from nsds_lab_to_nwb.components.electrode.electrode_groups_originator import ElectrodeGroupsOriginator
from nsds_lab_to_nwb.components.electrode.electrodes_originator import ElectrodesOriginator
from nsds_lab_to_nwb.components.neural_data.neural_data_originator import NeuralDataOriginator
from nsds_lab_to_nwb.components.stimulus.stimulus_originator import StimulusOriginator


path = os.path.dirname(os.path.abspath(__file__))

logging.config.fileConfig(fname=str(path) + '/logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


#TODO: GET ACCURATE START TIME
_DEFAULT_SESSION_START_TIME = datetime.fromtimestamp(0, pytz.utc) # dummy value for now


class NWBBuilder:
    '''Unpack data from a specified block, and write those data into NWB file format.
    '''

    def __init__(
            self,
            data_path: str,
            animal_name: str,
            block: str,
            nwb_metadata: MetadataManager,
            out_path: str = '',
            session_start_time = _DEFAULT_SESSION_START_TIME,
            use_htk = False
    ):
        self.data_path = data_path
        self.animal_name = animal_name
        self.block = block
        self.metadata = nwb_metadata.metadata
        self.out_path = out_path
        self.session_start_time = session_start_time
        self.use_htk = use_htk

        self.experiment_type = self.metadata['experiment_type'] # now required

        logger.info('Collecting relevant input data paths...')
        self.dataset = self._collect_dataset_paths()

        logger.info('Preparing output path...')
        rat_out_dir = os.path.join(self.out_path, self.animal_name)
        os.makedirs(rat_out_dir, exist_ok=True)
        self.output_file = os.path.join(rat_out_dir,
                                self.animal_name + '_' + self.block + '.nwb')

        logger.info('Creating originator instances...')
        self.device_originator = DeviceOriginator(self.metadata)
        self.electrode_groups_originator = ElectrodeGroupsOriginator(self.metadata)
        self.electrodes_originator = ElectrodesOriginator(self.metadata)
        self.neural_data_originator = NeuralDataOriginator(self.dataset, self.metadata, use_htk=self.use_htk)
        self.stimulus_originator = StimulusOriginator(self.dataset, self.metadata)


    def _collect_dataset_paths(self):
        # scan data_path and identify relevant subdirectories
        if self.experiment_type == 'auditory':
            data_scanner = AuditoryDataScanner(
                self.animal_name, self.block, data_path=self.data_path)
        elif self.experiment_type == 'behavior':
            raise ValueError('behavior data not yet supported.')
        else:
            raise ValueError('unknown experiment type')
        return data_scanner.extract_dataset()

    def build(self, process_stim=True):
        '''Build NWB file content.

        Parameters
        ----------
        use_htk: applicable for auditory datasets only.
                if False, use HTK files. if True, use TDT files directly.
        process_stim: (bool) default is True. optionally skip stimulus processing
                while developing/testing other features (temporary switch)

        Returns:
        --------
        nwb_content: an NWBFile object.
        '''
        logger.info('Building components for NWB')
        block_name = self.metadata['block_name']
        nwb_content = NWBFile(
            session_description=self.metadata['session_description'], # 'foo',
            experimenter=self.metadata['experimenter'],
            lab=self.metadata['lab'],
            institution=self.metadata['institution'],
            session_start_time = self.session_start_time,
            file_create_date=datetime.now(),
            identifier=str(uuid.uuid1()), # block_name,
            session_id=block_name,
            experiment_description=self.metadata['experiment_description'],
            subject=Subject(
                subject_id=self.metadata['subject']['subject id'],
                description=self.metadata['subject']['description'],
                genotype=self.metadata['subject']['genotype'],
                sex=self.metadata['subject']['sex'],
                species=self.metadata['subject']['species']
            ),
            notes=self.metadata.get('notes', None),
            pharmacology=self.metadata.get('pharmacology', None),
            surgery=self.metadata.get('surgery', None),
        )

        logger.info('Adding hardware information...')
        self.device_originator.make(nwb_content)
        self.electrode_groups_originator.make(nwb_content)
        electrode_table_regions = self.electrodes_originator.make(nwb_content)

        logger.info('Adding neural data...')
        self.neural_data_originator.make(nwb_content, electrode_table_regions)

        if process_stim:
            logger.info('Adding stimulus...')
            self.stimulus_originator.make(nwb_content)
        else:
            logger.info('Skipping stimulus...')

        return nwb_content

    def write(self, content):
        '''Write collected NWB content into an actual file.
        '''

        logger.info('Writing down content to ' + self.output_file)
        with NWBHDF5IO(path=self.output_file, mode='w') as nwb_fileIO:
            nwb_fileIO.write(content)
            nwb_fileIO.close()

        logger.info(self.output_file + ' file has been created.')
        return self.output_file
