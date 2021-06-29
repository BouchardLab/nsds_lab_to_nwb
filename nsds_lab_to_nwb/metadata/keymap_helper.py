from nsds_lab_to_nwb.metadata.resources import read_metadata_resource


def _remap_and_inject(metadata_parsed, old_key, value, mapto=None):
    if mapto is None:
        metadata_parsed[old_key] = value
        return
    if not isinstance(mapto, str):
        raise TypeError('Argument `mapto` should be a string.')
    # remap
    key_chain = mapto.split('.')    # list of strings; last item may be empty ''
    target = metadata_parsed
    for depth, new_key in enumerate(key_chain):
        if depth == len(key_chain) - 1:
            # if this is the last key in the chain, inject and return;
            # if new_key is an empty string, use old_key
            new_key = new_key if len(new_key) > 0 else old_key
            target[new_key] = value
            return
        # otherwise go down one layer
        if new_key not in target:
            target[new_key] = {}
        target = target[new_key]


def apply_keymap(metadata_input, keymap_file='metadata_keymap', key_for_unknown='other'):
    keymap = read_metadata_resource(keymap_file)

    metadata_parsed = {}
    for key, value in metadata_input.items():
        found_key = False
        for km in keymap['keymap']:
            if km['name'] == key:
                _remap_and_inject(metadata_parsed, key, value, mapto=km['mapto'])
                found_key = True
                break
        if not found_key:
            _remap_and_inject(metadata_parsed, key, value, mapto=f'{key_for_unknown}.')
    return metadata_parsed


if __name__ == '__main__':
    TEST_METADATA = {
        'lab': 'Bouchard Lab',
        'animal_name': 'RXX',
        'ecog_type': 'ecogXX',
        'poly_type': 'cambXX',
        'ecog': 'TRUE',
        'poly': 'FALSE',
        'notes': 'This is a test.'}
    metadata_parsed = apply_keymap(metadata_input=TEST_METADATA,
                                   keymap_file='metadata_keymap')
    print(metadata_parsed)
