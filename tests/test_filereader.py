import os
import pySWATPlus
import pytest
import typing


@pytest.fixture(scope='class')
def file_reader() -> typing.Generator[pySWATPlus.FileReader, None, None]:

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data', 'TxtInOut')
    data_file = os.path.join(data_folder, 'hydrology.hyd')

    # initializing FileReader class instance
    file_reader = pySWATPlus.FileReader(
        path=data_file
    )

    yield file_reader


def test_dataframe(
    file_reader: pySWATPlus.FileReader
) -> None:

    # read DataFrame
    df = file_reader.df
    assert df.shape[0] == 561

    # change varibale value
    variable = 'epco'
    value = 0.75
    df[variable] = value

    # rewrite the file
    file_reader.overwrite_file()

    # read the new DataFrame
    df = file_reader.df
    assert df[variable].unique()[0] == value

    # DataFrame parameter value change by 'absval'
    pySWATPlus.utils._apply_param_change(
        df=df,
        param_name='latq_co',
        change={'value': 0.6, 'change_type': 'absval', 'filter_by': 'name == "hyd001"'}
    )
    assert df.iloc[0, -1] == 0.6

    # DataFrame parameter value change by 'abschg'
    pySWATPlus.utils._apply_param_change(
        df=df,
        param_name='pet_co',
        change={'value': 0.6, 'change_type': 'abschg', 'filter_by': 'name == "hyd002"'}
    )
    assert df.loc[1, 'pet_co'] == 1.6

    # DataFrame parameter value change by 'pctchg'
    pySWATPlus.utils._apply_param_change(
        df=df,
        param_name='perco',
        change={'value': 50, 'change_type': 'pctchg', 'filter_by': 'name == "hyd003"'}
    )
    assert round(df.loc[2, 'perco'], 2) == 0.08


def test_dataframe_filterby(
) -> None:

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data', 'TxtInOut')
    data_file = os.path.join(data_folder, 'plants.plt')

    # initializing FileReader class instance
    file_reader = pySWATPlus.FileReader(
        path=data_file,
        filter_by='plnt_typ == "cold_annual"'
    )

    # DataFrame
    df = file_reader.df
    assert len(df) == 37


def test_error() -> None:

    # set up folder path
    test_folder = os.path.dirname(__file__)

    # error test for string or pathlib.Path object
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path=1
        )
    assert exc_info.value.args[0] == 'path must be a string or Path object'

    # error test for non-existence of file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path='not_exist_yr.txt'
        )
    assert exc_info.value.args[0] == 'file does not exist'

    # error test for CSV file extension
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path=os.path.join(test_folder, 'sample_data', 'no_exe', 'error_file.csv')
        )
    assert exc_info.value.args[0] == 'Not implemented yet'


def test_github() -> None:

    # regular GitHub trigger test function when no code is changed
    assert str(1) == '1'
