import re
import os
import numpy as np
import csv
import h5py

# import pkg_resources


class StimValueExtractor():
    def __init__(self, stim_values_command, stim_lib_path):
        self.stim_values_command = stim_values_command
        self.stim_lib_path = stim_lib_path

    def extract(self):
        stim_values_command = self.stim_values_command
        if 'tone_stimulus_values' in stim_values_command:
            extractor, filename = self.__parse_command(stim_values_command)
            if extractor != 'tone_stimulus_values':
                raise ValueError('parsing error')
            stim_values = eval('{}(\'{}\')'.format(extractor,
                            os.path.join(self.stim_lib_path, filename)))
        if 'timit_stimulus_values' in stim_values_command:
            extractor, filename = self.__parse_command(stim_values_command)
            if extractor != 'timit_stimulus_values':
                raise ValueError('parsing error')
            stim_values = eval('{}(\'{}\')'.format(extractor,
                            os.path.join(self.stim_lib_path, filename)))
        if 'gen_tone_stim_vals' in stim_values_command:
            extractor, _ = self.__parse_command(stim_values_command)
            if extractor != 'gen_tone_stim_vals':
                raise ValueError('parsing error')
            stim_values = eval('{}()'.format(extractor))
        if 'np.ones' in stim_values_command:
            stim_values = eval(stim_values_command)

        return stim_values

    def __parse_command(self, command):
        ''' return (a_a_a, b.b.b) by parsing string 'a_a_a(b.b.b)' '''
        res = re.match('(\S+)\((\S+)\)', command)
        return (res.group(1), res.group(2))



def tone_stimulus_values(mat_file_path):
    ''' adapted from mars.configs.block_directory '''
    sio = h5py.File(mat_file_path, 'r')
    stim_vals = np.array(sio['stimVls']).astype(int)
    stim_vals[0,:] = stim_vals[0,:]+8
    sio.close()
    return stim_vals

def timit_stimulus_values(csv_file_path):
    ''' adapted from mars.configs.block_directory '''
    # NOTE: this file timit998.txt is just a list of wav files.
    # TODO: also load from these wav files.
    stim_vals = []
    with open(csv_file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stim_vals.append(row['sample_id'])
    return stim_vals

def gen_tone_stim_vals():
    ''' exact copy from mars.configs.block_directory '''
    frqs = np.array([500, 577, 666, 769, 887, 1024, 1182, 
        1364, 1575, 1818, 2098, 2421, 2795, 3226, 3723, 
        4297, 4960, 5725, 6608, 7627, 8803, 10160, 11727, 
        13535, 15622, 18031, 20812, 24021, 27725, 32000])
    amps = np.arange(1,9)
    frqset, ampset = np.meshgrid(frqs,amps)
    frq_amp_pairs = np.array([ampset.flatten(), frqset.flatten()]).T
    np.random.seed(seed=1234) #Insure that the same order is produced with each call.
    shuffle_inds1 = np.random.permutation(np.arange(frq_amp_pairs.shape[0]))
    shuffle_inds2 = np.random.permutation(np.arange(frq_amp_pairs.shape[0]))
    stim_vals = np.concatenate((frq_amp_pairs[shuffle_inds1,:],frq_amp_pairs[shuffle_inds2,:]),axis=0)
    return stim_vals.T
