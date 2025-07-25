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


def test_attr_df(
    file_reader: pySWATPlus.FileReader
) -> None:

    # read DataFrame
    df = file_reader.df

    assert df.shape[0] == 260


def test_method_dataframe(
    file_reader: pySWATPlus.FileReader
) -> None:

    # read DataFrame
    df = file_reader.df

    # change varibale value
    variable = 'minp'
    value = 0.3
    df[variable] = value

    # rewrite the file
    file_reader.overwrite_file()

    # read the new DataFrame
    new_df = file_reader.df

    assert new_df[variable].unique()[0] == value


def test_error() -> None:

    # set up folder path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data')

    # error test for string or pathlib.Path object
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path=1,
            has_units=True
        )
    assert exc_info.value.args[0] == 'path must be a string or Path object'

    # error test for non-existence of file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path='not_exist_yr.txt',
            has_units=True
        )
    assert exc_info.value.args[0] == 'file does not exist'

    # error test for CSV file extension
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path=os.path.join(data_folder, 'error_sample.csv'),
            has_units=True
        )
    assert exc_info.value.args[0] == 'Not implemented yet'


def test_github() -> None:

    # regular GitHub trigger test function when no code is changed
    assert str(2) == '2'
