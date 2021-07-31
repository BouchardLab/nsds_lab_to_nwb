import pandas as pd
import os
from nsds_lab_to_nwb.utils import split_block_folder
from nsds_lab_to_nwb.common.io import write_yaml


class ExpNoteReader():
    """Class for parsing experiment notes

    Parameters
    ----------
    path : str
        Path or Google Sheets URL to the experiment notes
    block_folder : str
        Name of the block to parse for

    Raises
    ------
    Exception
        Raises exception when trying to parse xlsx or
        Google sheets because those parses are not
        implemented
    """

    def __init__(self, path, block_folder, input_format=None):
        self.path = path
        self.input_format = input_format
        self.block_folder = block_folder
        _, _, blockstr = split_block_folder(block_folder)
        self.block_id = int(blockstr[1:])
        self.file = []
        self._raw_meta = None
        self._raw_block = None

        no_file_flag = False
        # force input if specified
        if self.input_format is not None:
            if self.input_format != 'gs':
                path_contents = os.listdir(path)
                for file in path_contents:
                    if file.endswith('.' + self.input_format):
                        self.file.append(file)
                if len(self.file) == 0:
                    no_file_flag = True
        else:
            # autodetect input format
            if path.startswith('http'):
                self.input_format = 'gs'
            else:
                path_contents = os.listdir(path)
                for file in path_contents:
                    if file.endswith('.ods'): # priority for ods format
                        self.input_format = 'ods'
                        self.file.append(file)
                        break
                    if file.endswith('.xlsx'):
                        self.input_format = 'xlsx'
                        self.file.append(file)
                        break
                    if file.endswith('.csv'):
                        self.input_format = 'csv'
                        self.file.append(file)
                if len(self.file) == 0:
                    no_file_flag = True

        if no_file_flag:
            raise FileNotFoundError

        self.meta_df = None
        self.block_df = None
        self.meta_block_df = None
        self.nsds_meta = None

    def read_input(self):
        """Read input
        """
        if self.input_format == 'csv':
            self.read_csvs()
        elif self.input_format == 'xlsx':
            self.read_xlsx()
        elif self.input_format == 'gs':
            self.read_gs()
        elif self.input_format == 'ods':
            self.read_ods()
        self.parse_sheets()

    def parse_sheets(self):
        """Parse raw dataframes read from experiment notes
        """
        raw_meta = self._raw_meta
        raw_block = self._raw_block

        # clean up raw_meta
        raw_meta = raw_meta.iloc[:, 1]
        good_indices = raw_meta.index.dropna()
        raw_meta = raw_meta.loc[good_indices]

        # clean up raw_block
        max_row = len(raw_block)
        for idx, row in raw_block.iterrows():
            try:
                _ = int(row['block_id'])
            except ValueError:
                max_row = idx
                break

        for column in raw_block.columns:
            if column.startswith('Unnamed'):
                raw_block.drop(column, axis=1, inplace=True)
        raw_block = raw_block[:max_row]
        raw_block = raw_block.dropna(axis=1, how='all')

        self.meta_df = raw_meta
        self.block_df = raw_block

    def read_csvs(self):
        """Read csv files
        """
        # detect which csv is a block and which is meta based on
        # default name Google Drive assigns when downloading it
        if self.file[0].endswith('BlockData.csv'):
            block_file = self.file[0]
            meta_file = self.file[1]
        else:
            block_file = self.file[1]
            meta_file = self.file[0]

        meta_path_file = os.path.join(self.path, meta_file)
        block_path_file = os.path.join(self.path, block_file)
        raw_meta = pd.read_csv(meta_path_file,
                               delimiter=',',
                               skiprows=1,
                               index_col=1,
                               dtype=str)

        raw_block = pd.read_csv(block_path_file,
                                delimiter=',', header=2, dtype=str)
        self._raw_meta = raw_meta
        self._raw_block = raw_block

    def read_ods(self):
        """Read ods
        """
        path_file = os.path.join(self.path, self.file[0])
        raw_meta = pd.read_excel(path_file, sheet_name='MetaData', index_col=1,
                                 dtype=str,
                                 engine='odf')
        raw_block = pd.read_excel(path_file, sheet_name='BlockData',
                                  header=2,
                                  dtype=str,
                                  engine='odf')
        self._raw_meta = raw_meta
        self._raw_block = raw_block

    def read_xlsx(self):
        """Read xlsx
        """
        raise NotImplementedError('TODO')

    def read_gs(self):
        """Read Google Sheet

        Raises
        ------
        NotImplementedError
            ToDo
        """
        raise NotImplementedError('TODO')

    def merge_meta_block(self):
        """Merge meta and block dataframes and return as dictionary
        """
        sub_block = self.block_df[self.block_df['block_id'].astype(int) == self.block_id].transpose().to_dict()
        key = list(sub_block.keys())[0]
        sub_block = sub_block[key]
        meta = self.meta_df.to_dict()
        meta.update(sub_block)
        self.nsds_meta = meta

    def dump_yaml(self, write_path=None):
        """Dump yaml file

        Parameters
        ----------
        write_path : str, optional
            Path to write yaml file, by default None
            If None writes to self.path
        
        Returns
        -------
        write_path_file : path
            path file to written yaml
        """
        if write_path is None:
            write_path = self.path
        nsds_meta = self.get_nsds_meta()
        write_path_file = os.path.join(write_path, self.block_folder + '.yaml')
        write_yaml(write_path_file, nsds_meta, sort_keys=True)
        return write_path_file

    def get_nsds_meta(self):
        """Get parsed data

        Returns
        -------
        nsds_meta : dict
            Parsed meta data
        """
        if self.nsds_meta is None:
            self.read_input()
            self.merge_meta_block()
        return self.nsds_meta
