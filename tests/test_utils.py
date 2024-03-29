import pytest, os

from nsds_lab_to_nwb.utils import (get_data_path, get_metadata_lib_path, get_stim_lib_path,
                                   split_block_folder)


def test_split_block_folder():
    """Tests how 'block_folder' is split."""

    block_folder = 'RJL01_B02'
    fl, an, bn = split_block_folder(block_folder)
    assert fl == 'JL'
    assert an == 'RJL01'
    assert bn == 'B02'

    # legacy
    block_folder = 'R01_B02'
    fl, an, bn = split_block_folder(block_folder)
    assert fl is None
    assert an == 'R01'
    assert bn == 'B02'


def test_get_data_path():
    """Tests data_path function."""
    data_path = '/home/user/data'
    del os.environ['NSDS_DATA_PATH']
    assert data_path == get_data_path(data_path)
    with pytest.raises(ValueError):
        get_data_path(None)
    data_path2 = '/home/user/new_data'
    os.environ['NSDS_DATA_PATH'] = data_path2

    assert data_path == get_data_path(data_path)
    assert data_path2 == get_data_path(None)


def test_get_metadata_lib_path():
    """Tests metadata_lib_path function."""
    metadata_path = '/home/user/metadata'
    del os.environ['NSDS_METADATA_PATH']
    assert metadata_path == get_metadata_lib_path(metadata_path)
    with pytest.raises(ValueError):
        get_metadata_lib_path(None)
    metadata_path2 = '/home/user/new_metadata'
    os.environ['NSDS_METADATA_PATH'] = metadata_path2

    assert metadata_path == get_metadata_lib_path(metadata_path)
    assert metadata_path2 == get_metadata_lib_path(None)


def test_get_stim_lib_path():
    """Tests stim_lib_path function."""
    stim_path = '/home/user/stim'
    del os.environ['NSDS_STIMULI_PATH']
    assert stim_path == get_stim_lib_path(stim_path)
    with pytest.raises(ValueError):
        get_stim_lib_path(None)
    stim_path2 = '/home/user/new_stim'
    os.environ['NSDS_STIMULI_PATH'] = stim_path2

    assert stim_path == get_stim_lib_path(stim_path)
    assert stim_path2 == get_stim_lib_path(None)
