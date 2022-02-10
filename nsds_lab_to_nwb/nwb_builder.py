import logging.config
import sys
import os
import uuid
# import warnings

from pynwb import NWBHDF5IO, NWBFile
from pynwb.file import Subject

from nsds_lab_to_nwb.common.data_scanners import AuditoryDataScanner
from nsds_lab_to_nwb.common.time import (get_current_time, get_default_time,
                                         validate_time)
from nsds_lab_to_nwb.components.electrode.electrodes_originator import ElectrodesOriginator
from nsds_lab_to_nwb.components.neural_data.neural_data_originator import NeuralDataOriginator
from nsds_lab_to_nwb.components.stimulus.stimulus_originator import StimulusOriginator
from nsds_lab_to_nwb.metadata.metadata_manager import MetadataManager
from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path, get_stim_lib_path,
                                   split_block_folder, get_software_info, str2bool)

# basicConfig ignored if a filehandler is already set up (as in example scripts)
logging.basicConfig(stream=sys.stderr)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NWBBuilder:
    """Unpack data from a specified block, and write those data into NWB file format.

    Parameters
    ----------
    data_path : str
        Path to top level data folder.
    block_folder : str
        Block specification.
    save_path : str
        Path to save folder.
    block_metadata_path : str
        Path to block metadata file.
    metadata_lib_path : str
        Path to metadata library repo.
    stim_lib_path : str
        Path to stimulus library.
    metadata_save_path : str
        Path to (optionally) save metadata input as yaml files.
    resample_data : bool
        Resample neural data to the nearest kHz.
        Passed to resample_flag kwarg in NeuralDataOriginator.
    use_htk : bool
        Use data from HTK files.
    """

    def __init__(
            self,
            data_path: str,
            block_folder: str,
            save_path: str,
            block_metadata_path: str = None,
            metadata_lib_path: str = None,
            stim_lib_path: str = None,
            metadata_save_path: str = None,
            resample_data=False,
            use_htk=False
    ):
        self.data_path = get_data_path(data_path)
        self.metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.surgeon_initials, self.animal_name, self.block_name = split_block_folder(block_folder)
        self.block_folder = block_folder
        self.save_path = save_path
        self.block_metadata_path = self._get_block_metadata_path(block_metadata_path)
        self.metadata_save_path = metadata_save_path
        self.resample_data = resample_data
        self.use_htk = use_htk

        self.source_script, self.source_script_file_name = self._get_source_script()

        logger.info('==================================')
        logger.info(f'Processing block {block_folder}.')

        logger.info('Collecting metadata for NWB conversion...')
        self.metadata = self._collect_nwb_metadata()
        self.experiment_type = self.metadata['experiment_type']
        self.bad_block, incomplete_block = self._check_bad_block()
        if incomplete_block:
            self.bad_block = True
            logger.info('Incomplete block. Escaping __init__ before originators.')
            return

        logger.info('Collecting relevant input data paths...')
        self.dataset = self._collect_dataset_paths()

        logger.info('Preparing output path...')
        rat_out_dir = os.path.join(self.save_path, self.animal_name)
        os.makedirs(rat_out_dir, exist_ok=True)
        self.output_file = os.path.join(rat_out_dir, f'{self.block_folder}.nwb')

        logger.info('Creating originator instances...')
        self.electrodes_originator = ElectrodesOriginator(self.metadata)
        self.stimulus_originator = StimulusOriginator(self.dataset, self.metadata)
        self.neural_data_originator = NeuralDataOriginator(self.dataset, self.metadata,
                                                           resample_flag=self.resample_data)

        logger.info('Extracting session start time...')
        self.session_start_time = self._extract_session_start_time()

    def _get_block_metadata_path(self, block_metadata_path):
        if block_metadata_path is not None:
            return block_metadata_path

        if self.surgeon_initials is None:
            # legacy block
            return os.path.join(self.metadata_lib_path, 'auditory', 'legacy', 'yaml', 'block',
                                self.animal_name, f'{self.block_folder}.yaml')

        # new block
        return os.path.join(self.data_path, self.animal_name, self.block_folder,
                            f"{self.block_folder}.yaml")

    def _get_source_script(self):
        info = get_software_info()
        # if info['git_branch'] != 'main':
        #     warnings.warn(f"You are currently on the {info['git_branch']} branch "
        #                   f"of the {info['name']} git repository. " +
        #                   "Final NWB files should be created from the main branch.")
        source_script = (f"Created by nsds-lab-to-nwb {info['version']} "
                         f"({info['url']}) "
                         f"(git@{info['git_describe']})")
        source_script_file_name = 'nsds-lab-to-nwb'  # for now just report the package name
        return source_script, source_script_file_name

    def _collect_nwb_metadata(self):
        # collect metadata for NWB conversion
        self.metadata_manager = MetadataManager(
            block_folder=self.block_folder,
            block_metadata_path=self.block_metadata_path,
            metadata_lib_path=self.metadata_lib_path,
            stim_lib_path=self.stim_lib_path,
            metadata_save_path=self.metadata_save_path)
        return self.metadata_manager.extract_metadata()

    def _check_bad_block(self):
        bad_block = False
        incomplete_block = False
        extra_meta = self.metadata.get('extra_meta', {})
        if not str2bool(extra_meta.get('is_clean_block', True)):
            logger.info('* Bad block: experimenter reported clean_block=False')
            bad_block = True
        if self.metadata['stimulus']['name'] is None:
            logger.warning('* Incomplete block: missing stimulus name in metadata.'
                           'Perhaps use the baseline stimulus?')
            incomplete_block = True

        return bad_block, incomplete_block

    def _collect_dataset_paths(self):
        # scan data_path and identify relevant subdirectories
        if self.experiment_type == 'auditory':
            data_scanner = AuditoryDataScanner(self.block_folder,
                                               data_path=self.data_path,
                                               stim_lib_path=self.stim_lib_path,
                                               use_htk=self.use_htk)
        elif self.experiment_type == 'behavior':
            raise ValueError('behavior data not yet supported.')
        else:
            raise ValueError('unknown experiment type')
        return data_scanner.extract_dataset()

    def _extract_session_start_time(self):
        if self.use_htk:
            logger.info(' - Using a dummy session_start_time (HTK pipeline)')
            return get_default_time()

        # extract from TDT data
        recorded_metadata = self.neural_data_originator.neural_data_reader.get_info()
        session_start_time = recorded_metadata['start_date']
        return validate_time(session_start_time)

    def _add_extra_metadata(self, nwb_content):
        # temporary solution: add as scratch data
        extra_meta = self.metadata['extra_meta']
        for key, value in extra_meta.items():
            nwb_content.add_scratch(data=[value],
                                    name=key, notes=f'extra metadata {key}')

    def build(self, process_stim=True):
        '''Build NWB file content.

        Parameters
        ----------
        process_stim: (bool) default is True. optionally skip stimulus processing
                while developing/testing other features (temporary switch)

        Returns:
        --------
        nwb_content: an NWBFile object.
        '''
        if self.bad_block:
            logger.info('Looks like a bad block. Not building.')
            return

        logger.info('Building components for NWB')
        current_time = get_current_time()

        block_name = self.metadata['block_name']
        nwb_content = NWBFile(
            session_description=self.metadata['session_description'],
            experimenter=self.metadata['experimenter'],
            lab=self.metadata['lab'],
            institution=self.metadata['institution'],
            session_start_time=self.session_start_time,
            file_create_date=current_time,
            identifier=str(uuid.uuid1()),
            session_id=block_name,
            experiment_description=self.metadata['experiment_description'],
            subject=Subject(
                subject_id=self.metadata['subject']['subject_id'],
                description=self.metadata['subject']['description'],
                genotype=self.metadata['subject']['genotype'],
                sex=self.metadata['subject']['sex'],
                species=self.metadata['subject']['species'],
                weight=self.metadata['subject']['weight'],
            ),
            notes=self.metadata.get('notes', None),
            pharmacology=self.metadata.get('pharmacology', None),
            surgery=self.metadata.get('surgery', None),
            source_script=self.source_script,
            source_script_file_name=self.source_script_file_name,
        )

        logger.info('Adding extra metadata items...')
        self._add_extra_metadata(nwb_content)

        logger.info('Adding electrode information...')
        electrode_table_regions = self.electrodes_originator.make(nwb_content)

        logger.info('Adding neural data...')
        tdt_reader = self.neural_data_originator.make(nwb_content, electrode_table_regions)

        if process_stim:
            logger.info('Adding stimulus...')
            self.stimulus_originator.make(nwb_content, tdt_reader=tdt_reader)
        else:
            logger.info('Skipping stimulus...')


        logger.info('NWB content built successfully.')
        return nwb_content

    def write(self, content):
        '''Write collected NWB content into an actual file.
        '''
        if self.bad_block:
            logger.info('Looks like a bad block. Nothing to write.')
            return

        logger.info('Writing down content to ' + self.output_file)
        with NWBHDF5IO(path=self.output_file, mode='w') as nwb_fileIO:
            nwb_fileIO.write(content)

        logger.info(self.output_file + ' file has been created.')
        return self.output_file
