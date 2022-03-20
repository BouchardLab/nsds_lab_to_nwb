from nsds_lab_to_nwb.metadata.resources import read_metadata_resource


def check_stimulus_name(stim_name_input):
    stim_directory = read_metadata_resource('list_of_stimuli')

    if stim_name_input in stim_directory.keys():
        # if there is a matching key, just read the corresponding entry
        return stim_name_input, stim_directory[stim_name_input]
    # if stim_name does not match any key, try the alternative names
    for key, stim_info in stim_directory.items():
        for alt_name in stim_info['alt_names']:
            if stim_name_input == alt_name:
                return key, stim_info
    raise ValueError(f"Stimulus type '{stim_name_input}' not found.")


def get_stimulus_metadata(stim_name_input):
    _, stim_info = check_stimulus_name(stim_name_input)
    return stim_info
