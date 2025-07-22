import os
import pySWATPlus
import pytest


@pytest.fixture(scope='class')
def file_reader():

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data')
    data_file = os.path.join(data_folder, 'aquifer_yr.txt')

    # DataFrame from input data file
    file_reader = pySWATPlus.FileReader(
        path=data_file,
        has_units=True
    )

    yield file_reader


def test_get_df(
    file_reader
):

    # read DataFrame
    df = file_reader.df

    assert df.shape[0] == 260


def test_github():

    # regular GitHub trigger test function when no code is changed
    assert str(1) == '1'
