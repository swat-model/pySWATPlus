import os
import pySWATPlus
import pytest
import typing


@pytest.fixture(scope='class')
def file_reader() -> typing.Generator[pySWATPlus.FileReader, None, None]:

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data')
    data_file = os.path.join(data_folder, 'aquifer_yr.txt')

    # initializing FileReader class instance
    file_reader = pySWATPlus.FileReader(
        path=data_file,
        has_units=True
    )

    yield file_reader


def test_get_df(
    file_reader: pySWATPlus.FileReader
) -> None:

    # read DataFrame
    df = file_reader.df

    assert df.shape[0] == 260


def test_github() -> None:

    # regular GitHub trigger test function when no code is changed
    assert str(2) == '2'
