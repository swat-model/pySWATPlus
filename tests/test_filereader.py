import os
import pySWATPlus


def test_filereader():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initializing FileReader class instance
    file_reader = pySWATPlus.FileReader(
        path=os.path.join(txtinout_folder, 'hydrology.hyd'),
        has_units=False,
    )

    # pass test for DataFrame attribute
    df = file_reader.df
    assert df.shape[0] == 561


def test_github():

    # GitHub test function tigger when no code is changed
    assert str(2) == '2'
