import os
import shutil
import pySWATPlus
import pytest
import tempfile


def test_filereader_and_error():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initializing FileReader class instance
    file_reader = pySWATPlus.FileReader(
        path=os.path.join(txtinout_folder, 'hydrology.hyd')
    )

    # pass test for DataFrame attribute
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

    # pass test for DataFrame parameter value change by 'absval'
    pySWATPlus.utils._apply_param_change(
        df=df,
        param_name='latq_co',
        change={'value': 0.6, 'filter_by': 'name == "hyd001"'}
    )
    assert df.iloc[0, -1] == 0.6

    # pass test for DataFrame parameter value change by 'abschg'
    pySWATPlus.utils._apply_param_change(
        df=df,
        param_name='pet_co',
        change={'value': 0.6, 'change_type': 'abschg', 'filter_by': 'name == "hyd002"'}
    )
    assert df.loc[1, 'pet_co'] == 1.6

    # pass test for DataFrame parameter value change by 'pctchg'
    pySWATPlus.utils._apply_param_change(
        df=df,
        param_name='perco',
        change={'value': 50, 'change_type': 'pctchg', 'filter_by': 'name == "hyd003"'}
    )
    assert round(df.loc[2, 'perco'], 2) == 0.08

    # pass test for filtering DataFrame by query string
    file_reader = pySWATPlus.FileReader(
        path=os.path.join(txtinout_folder, 'plants.plt'),
        filter_by='plnt_typ == "cold_annual"'
    )
    df = file_reader.df
    assert len(df) == 37

    with tempfile.TemporaryDirectory() as tmp_dir:
        # pass test for rewriting empty DataFrame in a TXT file
        file_name = 'topography.hyd'
        shutil.copy2(
            src=os.path.join(txtinout_folder, file_name),
            dst=os.path.join(tmp_dir, file_name)
        )
        file_reader = pySWATPlus.FileReader(
            path=os.path.join(tmp_dir, file_name),
            filter_by='name == "topohru000"'
        )
        df = file_reader.df
        assert len(df) == 0
        file_reader.overwrite_file()
        # pass test for rewriting DataFrame with 'has_units' key in a TXT file
        file_name = 'basin_carbon_all.txt'
        shutil.copy2(
            src=os.path.join(txtinout_folder, file_name),
            dst=os.path.join(tmp_dir, file_name)
        )
        file_reader = pySWATPlus.FileReader(
            path=os.path.join(tmp_dir, file_name),
            has_units=True
        )
        df = file_reader.df
        assert len(df) == 0
        file_reader.overwrite_file()

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
                path=os.path.join(txtinout_folder, 'zerror_aa.csv')
            )
        assert exc_info.value.args[0] == 'Not implemented yet'


def test_github():

    # regular GitHub trigger test function when no code is changed
    assert str(1) == '1'
