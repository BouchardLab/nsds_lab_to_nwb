import logging
import os
import numpy as np
from nsds_lab_to_nwb.utils import (get_metadata_lib_path, get_stim_lib_path,
                                   split_block_folder)

from nsds_lab_to_nwb.common.io import read_yaml, write_yaml
from nsds_lab_to_nwb.metadata.exp_note_reader import ExpNoteReader
from nsds_lab_to_nwb.metadata.keymap_helper import apply_keymap
from nsds_lab_to_nwb.metadata.resources import read_metadata_resource
from nsds_lab_to_nwb.metadata.stim_name_helper import check_stimulus_name


_DEFAULT_EXPERIMENT_TYPE = 'auditory'

logger = logging.getLogger(__name__)


class MetadataReader:
    ''' Reads metadata input for new experiments.
    '''
    def __init__(self,
                 block_metadata_path: str,
                 metadata_lib_path: str,
                 block_folder: str,
                 metadata_save_path=None,
                 ):
        self.block_metadata_path = block_metadata_path
        self.metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
        self.block_folder = block_folder
        _, self.animal_name, _ = split_block_folder(block_folder)
        self.metadata_save_path = metadata_save_path

    def read(self):
        self.metadata_input = self.load_metadata_source()
        if self.metadata_save_path is not None:
            write_yaml(f'{self.metadata_save_path}/{self.block_folder}_metadata_input.yaml',
                       self.metadata_input)

        self.parse()
        self.common_check()
        self.extra_cleanup()
        if self.metadata_save_path is not None:
            write_yaml(f'{self.metadata_save_path}/{self.block_folder}_metadata_input_clean.yaml',
                       self.metadata_input)

        return self.metadata_input

    def load_metadata_source(self):
        try:
            metadata_input = read_yaml(self.block_metadata_path)
        except FileNotFoundError:
            # first generate the block metadata file
            experiment_path, block_metadata_file = os.path.split(self.block_metadata_path)
            block_folder, ext = os.path.splitext(block_metadata_file)
            reader = ExpNoteReader(experiment_path, block_folder)
            reader.dump_yaml(write_path=self.block_metadata_path)
            # then try reading again
            metadata_input = read_yaml(self.block_metadata_path)
        return metadata_input

    def parse(self):
        self.metadata_input = apply_keymap(self.metadata_input.copy(),
                                           keymap_file='metadata_keymap')

    def common_check(self):
        ''' make sure that core fields exist before further expanding metadata components.
        common for both new and legacy pipelines.
        '''
        if 'subject' not in self.metadata_input:
            self.metadata_input['subject'] = {}
            self.metadata_input['subject']['subject_id'] = self.animal_name

        # fix subject weight unit - always 'g' in our case
        subject_metadata = self.metadata_input['subject']
        if 'weight' in subject_metadata:
            weight = str(subject_metadata['weight'])
            if 'g' not in weight:
                subject_metadata['weight'] = f'{weight}g'

        if 'session_description' not in self.metadata_input:
            try:
                self.metadata_input['session_description'] = self.metadata_input['stimulus']['name']
            except KeyError:
                self.metadata_input['session_description'] = 'Unknown'

        device_metadata = self.metadata_input['device']
        for key in ('ECoG', 'Poly'):
            # required for ElectrodeGroup component
            if 'description' not in device_metadata[key]:
                device_metadata[key]['description'] = device_metadata[key]['name']
            if 'location' not in device_metadata[key]:
                # NEED: anatomical location in the brain, such as 'V1' or 'CA3'
                # perhaps something like 'AC' or 'A1' in our cases?
                device_metadata[key]['location'] = ''
            if 'location_details' not in device_metadata[key]:
                # more quantitative information
                device_metadata[key]['location_details'] = ''

            # required for Electrode component
            if 'imp' not in device_metadata[key]:
                # TODO: include impedance value
                device_metadata[key]['imp'] = np.nan
            if 'filtering' not in device_metadata[key]:
                device_metadata[key]['filtering'] = (
                    'The signal is low pass filtered at 45 percent of the sample rate, '
                    'and high pass filtered at 2 Hz.')

    def extra_cleanup(self):
        device_metadata = self.metadata_input['device']
        block_meta = self.metadata_input['block_meta']

        # if a device was not actually used in this block, drop the corresponding metadata
        default_value = False
        has_ecog = self.__convert_bool(block_meta.get('has_ecog', default_value))
        has_poly = self.__convert_bool(block_meta.get('has_poly', default_value))
        if not has_ecog:
            device_metadata.pop('ECoG')
        if not has_poly:
            device_metadata.pop('Poly')

        # device location metadata
        if has_ecog:
            ecog_lat_loc = device_metadata['ECoG'].pop('ecog_lat_loc', None)
            ecog_post_loc = device_metadata['ECoG'].pop('ecog_post_loc', None)
            if (ecog_lat_loc is not None) and (ecog_post_loc is not None):
                device_metadata['ECoG']['location_details'] = (
                    f'{ecog_lat_loc} mm from lateral ridge '
                    f'and {ecog_post_loc} mm from posterior ridge.')
        if has_poly:
            device_metadata['Poly']['location_details'] = 'Within the ECoG grid.'

    def __convert_bool(self, s):
        """Convert a True/False text (string) to a boolean value.

        Parameters
        ---------
        s : bool, str or int
            Something equivalent to True or False.

        Returns
        -------
        A corresponding boolean variable.
        """
        if isinstance(s, bool):
            return s
        if isinstance(s, int):
            return bool(s)
        if not isinstance(s, str):
            raise TypeError('Allowed types are bool, int or string.')

        # simply search from a word pool
        if s.lower() in ['true', '1', 't', 'y', 'yes']:
            return True
        if s.lower() in ['false', '0', 'f', 'n', 'no']:
            return False
        raise ValueError('Cannot convert \'{}\' to boolean.'.format(s))


class LegacyMetadataReader(MetadataReader):
    ''' Reads metadata input for old experiments.
    '''
    def __init__(self,
                 block_metadata_path: str,
                 metadata_lib_path: str,
                 block_folder: str,
                 metadata_save_path=None,
                 ):
        super().__init__(block_metadata_path, metadata_lib_path,
                         block_folder, metadata_save_path)

        self.experiment_type = 'auditory'   # for legacy auditory datasets

        # TODO: separate (experiment, device) metadata library as legacy
        self.legacy_lib_path = os.path.join(self.metadata_lib_path, self.experiment_type, 'yaml')

    def load_metadata_source(self):
        # direct input from the block yaml file (not yet expanded)
        metadata_input = read_yaml(self.block_metadata_path)

        # load from metadata library (legacy structure)
        for key in ('experiment', 'device'):
            logger.info(f'expanding {key} from legacy metadata library...')
            filename = metadata_input.pop(key)
            ref_data = read_yaml(
                os.path.join(self.legacy_lib_path, key, f'{filename}.yaml'))
            ref_data.pop('name', None)
            metadata_input.update(ref_data)
        return metadata_input

    def parse(self):
        self.metadata_input = apply_keymap(self.metadata_input.copy(),
                                           keymap_file='metadata_keymap_legacy')

    def extra_cleanup(self):
        # fill in old subject information
        old_subject_input = read_metadata_resource('old_subject_metadata')
        old_subject_metadata = old_subject_input['subject_metadata']
        old_subject_metadata['weight'] = old_subject_input['weights'].get(self.animal_name, 'Unknown')
        for key in old_subject_metadata:
            if key not in self.metadata_input['subject']:
                self.metadata_input['subject'][key] = old_subject_metadata[key]

        # put bad_chs to right places
        bad_chs_dict = self.metadata_input['device'].pop('bad_chs', None)
        if bad_chs_dict is not None:
            for dev_name, bad_chs in bad_chs_dict.items():
                self.metadata_input['device'][dev_name]['bad_chs'] = bad_chs

        # final touches...
        if self.experiment_type == 'auditory':
            self.metadata_input['experiment_description'] = 'Auditory experiment'
        if ('session_description' not in self.metadata_input
                or len(self.metadata_input['session_description']) == 0):
            self.metadata_input['session_description'] = (
                'Auditory experiment with {} stimulus'.format(self.metadata_input['stimulus']['name']))


class MetadataManager:
    """Manages metadata for NWB file builder

    Parameters
    ----------
    block_metadata_path : str
        Path to block metadata file.
    metadata_lib_path : str
        Path to metadata library repo.
    stim_lib_path : str
        Path to stimulus library.
    block_folder : str
        Block specification.
    metadata_save_path : str (optional)
        Path to a directory where parsed metadata file(s) will be saved.
        Files are saved only if metadata_save_path is provided.
    experiment_type : str (optional)
        Experiment type within the NSDS Lab: 'auditory' (default) or 'behavior'.
    legacy_block : bool (optional)
        Indicates whether this is a legacy block.
        If not provided, auto-detect by the metadata file extension (CAVEAT: no longer accurate)

    """
    def __init__(self,
                 block_metadata_path: str,
                 metadata_lib_path=None,
                 stim_lib_path=None,
                 block_folder=None,
                 metadata_save_path=None,
                 experiment_type=_DEFAULT_EXPERIMENT_TYPE,
                 legacy_block=None,
                 ):
        self.block_metadata_path = block_metadata_path
        self.metadata_lib_path = get_metadata_lib_path(metadata_lib_path)
        self.stim_lib_path = get_stim_lib_path(stim_lib_path)
        self.block_folder = block_folder
        self.surgeon_initials, self.animal_name, self.block_tag = split_block_folder(block_folder)
        self.metadata_save_path = metadata_save_path
        self.experiment_type = experiment_type
        self.yaml_lib_path = os.path.join(self.metadata_lib_path, self.experiment_type, 'yaml/')
        self.__detect_legacy_block(legacy_block)

        if self.metadata_save_path is not None:
            os.makedirs(self.metadata_save_path, exist_ok=True)

        if self.legacy_block:
            self.metadata_reader = LegacyMetadataReader(
                block_metadata_path=self.block_metadata_path,
                metadata_lib_path=self.metadata_lib_path,
                block_folder=self.block_folder,
                metadata_save_path=self.metadata_save_path)
        else:
            self.metadata_reader = MetadataReader(
                block_metadata_path=self.block_metadata_path,
                metadata_lib_path=self.metadata_lib_path,
                block_folder=self.block_folder,
                metadata_save_path=self.metadata_save_path)

    def __detect_legacy_block(self, legacy_block=None):
        if (legacy_block is not None):
            self.legacy_block = legacy_block
            return

        # detect which pipeline is used, based on animal naming scheme
        if self.surgeon_initials is not None:
            self.legacy_block = False
        else:
            self.legacy_block = True

    def extract_metadata(self):
        metadata_input = self.metadata_reader.read()

        metadata = self._extract(metadata_input)

        if self.metadata_save_path is not None:
            write_yaml(f'{self.metadata_save_path}/{self.block_folder}_metadata_full.yaml',
                       metadata)

        return metadata

    def _extract(self, metadata_input):
        metadata_input['experiment_type'] = self.experiment_type

        metadata = {}
        metadata['block_name'] = self.block_folder

        input_block_name = metadata_input.pop('name', None)
        if (input_block_name is not None) and input_block_name != metadata['block_name']:
            metadata['block_name_in_source'] = input_block_name

        # extract and add metadata fields in this order
        for key in ('experimenter', 'lab', 'institution',
                    'experiment_description', 'session_description',
                    'subject', 'surgery', 'pharmacology', 'notes',
                    'experiment_meta', 'experiment_type',
                    'stimulus', 'block_meta',
                    'device'
                    ):
            value = metadata_input.pop(key, None)
            if value is None:
                continue
            if key == 'stimulus':
                self.__load_stimulus_info(value)
            if key == 'device':
                self.__load_probes(value)
            metadata[key] = value

        # extract all remaining fields
        for key, value in metadata_input.items():
            logger.info(f'WARNING - unknown metadata field {key}')
            metadata[key] = value

        # final validation
        self.__check_subject(metadata)

        return metadata

    def __check_subject(self, metadata):
        if 'subject' not in metadata:
            metadata['subject'] = {}
        if 'subject_id' not in metadata['subject']:
            metadata['subject']['subject_id'] = self.animal_name
        if 'species' not in metadata['subject']:
            if metadata['subject']['subject_id'][0] == 'R':
                metadata['subject']['species'] = 'Rat'
        for key in ('description', 'genotype', 'sex', 'weight'):
            if key not in metadata['subject']:
                metadata['subject'][key] = 'Unknown'

    def __load_stimulus_info(self, stimulus_metadata):
        stim_name, _ = check_stimulus_name(stimulus_metadata['name'])
        if stim_name != stimulus_metadata['name']:
            stimulus_metadata['alt_name'] = stimulus_metadata['name']
        stim_yaml_path = os.path.join(self.yaml_lib_path, 'stimulus', stim_name + '.yaml')
        stimulus_metadata.update(read_yaml(stim_yaml_path))

    def __load_probes(self, device_metadata):
        for key, value in device_metadata.items():
            if key in ('ECoG', 'Poly'):
                if isinstance(value, str):
                    device_metadata[key] = {'name': value}
                probe_name = device_metadata[key]['name']
                probe_path = os.path.join(self.yaml_lib_path, 'probe', probe_name + '.yaml')
                device_metadata[key].update(read_yaml(probe_path))

                # TODO/CONSIDER: apply offset to all poly ch_pos systematically?
                # (using device_metadata['Poly']['poly_ap_loc']
                # and device_metadata['Poly']['poly_dev_loc'])

                # format device description
                nchannels, device_type, manufacturer = (
                    device_metadata[key]['nchannels'],
                    device_metadata[key]['device_type'],
                    device_metadata[key]['manufacturer'])
                device_metadata[key]['description'] = (
                    f'{nchannels}-ch {key} '
                    f'from {manufacturer} '
                    f'({device_type})')

                # add device location if not already specified
                if ('location' not in device_metadata[key] or
                        len(device_metadata[key]['location']) == 0):
                    if self.experiment_type == 'auditory':
                        device_metadata[key]['location'] = 'AUD'
