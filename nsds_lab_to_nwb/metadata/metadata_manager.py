import os
import io
import json
import yaml
import csv
import pandas as pd

# from nsds_lab_to_nwb.components.stimulus.stim_value_extractor import StimValueExtractor

_DEFAULT_EXPERIMENT_TYPE = 'auditory' # for legacy sessions


class MetadataManager:
    '''Manages metadata for NWB file builder
    '''

    def __init__(self,
                 block_metadata_path: str,
                 library_path: str,
                 stim_lib_path = None,
                 block_name = None,
                 animal_name = None,
                 use_old_pipeline = None,
                 ):
        self.block_metadata_path = block_metadata_path
        self.library_path = library_path
        self.animal_name = animal_name
        self.__detect_which_pipeline(use_old_pipeline)

        self.read_block_metadata_file(block_name=block_name)
        if self.animal_name is None:
            self.animal_name = self.block_name.split('_')[0]

        # paths to metadata/stimulus library
        self.yaml_lib_path = os.path.join(self.library_path, self.experiment_type, 'yaml/')
        # if (stim_lib_path is None) and (self.experiment_type == 'auditory'):
        #     stim_lib_path = os.path.join(self.library_path, self.experiment_type,
        #             'configs_legacy/mars_configs/') # <<<< should move to a better subfolder
        self.stim_lib_path = stim_lib_path

    def __detect_which_pipeline(self, use_old_pipeline):
        if (use_old_pipeline is not None) and isinstance(use_old_pipeline, bool):
            self.use_old_pipeline = use_old_pipeline
            return

        # detect which pipeline is used, based on metadata format
        _, ext = os.path.splitext(self.block_metadata_path)
        if ext in ('.yaml', '.yml'):
            self.use_old_pipeline = True
        elif ext == '.csv':
            self.use_old_pipeline = False
        else:
            raise ValueError('unknown block metadata format')

    def read_block_metadata_file(self,
            block_name=None,
            default_experiment_type=_DEFAULT_EXPERIMENT_TYPE):

        if self.use_old_pipeline:
            # direct input from the block yaml file (not yet expanded)
            self.block_metadata_input = self.read_yaml(self.block_metadata_path)
        else:
            block_id = int(block_name.split('_B')[1])
            self.block_metadata_input = self.read_csv_row(self.block_metadata_path, block_id)

        self.block_name = self.block_metadata_input.pop('name', block_name)

        # new requirement for nsdslab data: experiment_type
        self.experiment_type = self.block_metadata_input.pop('experiment_type', default_experiment_type)

        if self.use_old_pipeline:
            return
        self.__extend_experiment_and_device_metadata_new_pipeline()

    def __extend_experiment_and_device_metadata_new_pipeline(self):
        # this is somewhat ad hoc.
        # new metadata pipeline will be updated in the near future

        # unpack experiment
        experiment_metadata_path = os.path.join(
            os.path.dirname(self.block_metadata_path), 'meta_data.csv')
        experiment_metadata_input = self.csv_to_dict(experiment_metadata_path)

        device_metadata_input = self.__separate_device_metadata(experiment_metadata_input)
        self.block_metadata_input['experiment'] = experiment_metadata_input
        self.block_metadata_input['device'] = device_metadata_input

        # separate stimulus metadata
        if 'stim' in self.block_metadata_input:
            self.block_metadata_input['stimulus'] = {'name': self.block_metadata_input.pop('stim')}

    def __separate_device_metadata(self, metadata_input):
        device_metadata = {}
        for key in metadata_input.copy():
            if ('ecog_' in key) or ('poly_' in key):
                value = metadata_input.pop(key)
                if key == 'ecog_type':
                    device_metadata['ECoG'] = value
                if key == 'poly_type':
                    device_metadata['Poly'] = value
                device_metadata[key] = value
        return device_metadata

    def extract_metadata(self):
        metadata = {}
        metadata['block_name'] = self.block_name
        metadata['experiment_type'] = self.experiment_type

        # # expand metadata parts by extracting from library
        for key, value in self.block_metadata_input.items():
            if key == 'experiment':
                self.expand_experiment(metadata, value)
                continue
            if key == 'device':
                self.expand_device(metadata, value)
                continue
            if key == 'stimulus':
                if self.experiment_type != 'auditory':
                    raise ValueError('experiment type mismatch')
                self.expand_stimulus(metadata, value)
                continue
            # else:
            # --- ad hoc for new version ---
            # if key == 'stim':
            #     metadata['stimulus'] = {'name': self.block_metadata_input['stim']}
            # ---
            metadata[key] = value

        # --- ad hoc ---
        # # unpack experiment
        # experiment_metadata_path = os.path.join(
        #     os.path.dirname(self.block_metadata_path), 'meta_data.csv')
        # metadata['experiment'] = self.csv_to_dict(experiment_metadata_path)

        # # unpack device
        # self.__load_probes(metadata['device'])
        # ---

        # set experiment description
        if self.experiment_type == 'auditory':
            metadata['experiment_description'] = metadata['stimulus']['name'] + ' Stimulus Experiment'
        elif self.experiment_type == 'behavior':
            metadata['experiment_description'] = 'Reaching Experiment' # <<<< any additional specification?
        else:
            metadata['experiment_description'] = 'Unknown'

        # set session description, if not already existing
        if not metadata.get('session_description', None):
            metadata['session_description'] = metadata['experiment_description']
        return metadata

    def extract_metadata_old(self):
        metadata = {}
        metadata['block_name'] = self.block_name
        metadata['experiment_type'] = self.experiment_type

        # expand metadata parts by extracting from library
        for key, value in self.block_metadata_input.items():
            if key == 'experiment':
                self.expand_experiment(metadata, value)
                continue
            if key == 'device':
                self.expand_device(metadata, value)
                continue
            if key == 'stimulus':
                if self.experiment_type != 'auditory':
                    raise ValueError('experiment type mismatch')
                self.expand_stimulus(metadata, value)
                continue
            # else:
            metadata[key] = value

        # set experiment description
        if self.experiment_type == 'auditory':
            metadata['experiment_description'] = metadata['stimulus']['name'] + ' Stimulus Experiment'
        elif self.experiment_type == 'behavior':
            metadata['experiment_description'] = 'Reaching Experiment' # <<<< any additional specification?
        else:
            metadata['experiment_description'] = 'Unknown'

        # set session description, if not already existing
        if not metadata['session_description']:
            metadata['session_description'] = metadata['experiment_description']
        return metadata

    def expand_experiment(self, metadata, filename, key='experiment'):
        if isinstance(filename, str):
            ref_data = self.read_yaml(os.path.join(
                            self.yaml_lib_path, key, filename + '.yaml'))
        elif isinstance(filename, dict):
            ref_data = filename
        ref_data.pop('name', None)
        metadata.update(ref_data)  # add to top level
        self.__check_subject(metadata)

    def expand_device(self, metadata, filename, key='device'):
        if isinstance(filename, str):
            ref_data = self.read_yaml(os.path.join(
                            self.yaml_lib_path, key, filename + '.yaml'))
        elif isinstance(filename, dict):
            ref_data = filename
        self.__load_probes(ref_data)
        metadata[key] = ref_data

    def expand_stimulus(self, metadata, filename, key='stimulus'):
        if isinstance(filename, str):
            ref_data = self.read_yaml(os.path.join(
                            self.yaml_lib_path, key, filename + '.yaml'))
        elif isinstance(filename, dict):
            ref_data = filename

        # self.__load_stim_values(ref_data) # <<< now moved to WavManager
        ref_data['stim_lib_path'] = self.stim_lib_path # pass stim library path (ad hoc)

        metadata[key] = ref_data

    def __check_subject(self, metadata):
        if 'subject' not in metadata:
            metadata['subject'] = {}
        if 'subject id' not in metadata['subject']:
            metadata['subject']['subject id'] = self.animal_name
        if 'species' not in metadata['subject']:
            if metadata['subject']['subject id'][0] == 'R':
                metadata['subject']['species'] = 'Rat'
        for key in ('description', 'genotype', 'sex'):
            if key not in metadata['subject']:
                metadata['subject'][key] = 'Unknown'

    def __load_probes(self, device_metadata):
        for key, value in device_metadata.items():
            if key in ('ECoG', 'Poly'):
                probe_path = os.path.join(self.yaml_lib_path, 'probe', value + '.yaml')
                device_metadata[key] = self.read_yaml(probe_path)

    def __load_stim_values(self, stimulus_metadata):
        '''load stim_values from .mat or .csv files,
        or generate using original script (mars/configs/block_directory.py)
        '''
        # --- skip this for now; extract in NWB builder if necessary ---
        # stimulus_metadata['stim_values'] = StimValueExtractor(
        #     stimulus_metadata['stim_values'], self.stim_lib_path
        #     ).extract()
        pass


    @staticmethod
    def read_yaml(file_path):
        with open(file_path, 'r') as stream:
            metadata_dict = yaml.safe_load(stream)
            metadata = json.loads(json.dumps(metadata_dict)) #, parse_int=str, parse_float=str)
            return metadata

    @staticmethod
    def read_csv_row(file_path, block_id):
        all_blocks = pd.read_csv(file_path)
        blk_row = all_blocks.loc[all_blocks['block_id'] == block_id] # single row of DataFrame
        blk_dict = blk_row.to_dict(orient='records')[0] # a dict
        return blk_dict

    @staticmethod
    def csv_to_dict(csv_file):
        with open(csv_file, mode='r') as infile:
            reader = csv.reader(infile)
            mydict = {rows[0]:rows[1] for rows in reader}
        # skip header
        if ('key', 'value') in mydict.items():
            mydict.pop('key')
        return mydict
