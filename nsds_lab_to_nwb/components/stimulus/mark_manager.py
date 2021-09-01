from pynwb import TimeSeries

from nsds_lab_to_nwb.tools.htk.readers.htkfile import HTKFile
from nsds_lab_to_nwb.tools.tdt.tdt_reader import TDTReader


class MarkManager():
    def __init__(self, dataset):
        self.dataset = dataset

    def get_mark_track(self, starting_time, name='recorded_mark'):
        # Read the mark track
        if hasattr(self.dataset, 'htk_mark_path'):
            mark_file = HTKFile(self.dataset.htk_mark_path)
            mark_track, meta = mark_file.read_data()
            rate = mark_file.sample_rate
            mark_onsets = None
        else:
            tdt_reader = TDTReader(self.dataset.tdt_path)
            mark_track, meta = tdt_reader.get_data(stream='mrk1')
            rate = meta['sample_rate']
            mark_onsets = tdt_reader.get_events()

        # Create the mark timeseries
        mark_time_series = TimeSeries(name=name,
                                      data=mark_track,
                                      unit='Volts',
                                      starting_time=starting_time,
                                      rate=rate,
                                      description='The stimulus mark track.')

        return mark_time_series, mark_onsets
