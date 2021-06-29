import importlib.resources
import os

from nsds_lab_to_nwb.common.io import read_yaml


def read_metadata_resource(yaml_file):
    filename, ext = os.path.splitext(yaml_file)
    if ext not in ('.yaml', '.yml', ''):
        raise ValueError('yaml file expected')
    # force .yaml if extension is not provided
    yaml_file = f'{filename}.yaml'
    with importlib.resources.path('nsds_lab_to_nwb.metadata.resources', yaml_file) as data_path:
        resource = read_yaml(data_path)
    return resource
