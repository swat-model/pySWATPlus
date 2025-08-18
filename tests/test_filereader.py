import os
import shutil
import pySWATPlus
import pytest
import tempfile
import pandas


def test_filereader_and_error():

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

    with tempfile.TemporaryDirectory() as tmp_dir:
        # pass test for rewriting empty DataFrame in a TXT file
        file_name = 'hru_soilc_stat.txt'
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
            path=1,
            has_units=False
        )
    assert exc_info.value.args[0] == 'path must be a string or Path object'

    # error test for non-existence of file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.FileReader(
            path='not_exist_yr.txt',
            has_units=False
        )
    assert exc_info.value.args[0] == 'file does not exist'


def test_simulated_outputs():
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    txtinout_reader.enable_object_in_print_prt(
        obj=None,
        daily=True,
        monthly=True,
        yearly=True,
        avann=False
    )

    txtinout_reader.enable_csv_print()

    with tempfile.TemporaryDirectory() as tmp_dir:
        output = txtinout_reader.run_swat_in_other_dir(
            target_dir=tmp_dir,
            begin_and_end_year=(2010, 2012),
            warmup=1,
        )

        # error for overwriting output file
        with pytest.raises(Exception) as exc_info:
            file_reader = pySWATPlus.FileReader(
                path=output / 'channel_sd_yr.txt',
                has_units=True
            )
            file_reader.overwrite_file()
        assert exc_info.value.args[0] == 'Overwriting SWAT+ Output Files is not allowed'

        # ensure types are parsed correctly (for example jday must be int)
        file_reader = pySWATPlus.FileReader(
            path=output / 'channel_sd_yr.txt',
            has_units=True
        )
        assert pandas.api.types.is_integer_dtype(file_reader.df['jday'])

        # check that
        file_reader_csv = pySWATPlus.FileReader(
            path=output / 'channel_sd_yr.csv',
            has_units=True
        )

        # csv and txt decimals are rounded differently, so cannot be compared directly, just evaluate the shape
        assert file_reader.df.shape == file_reader_csv.df.shape, "Shapes differ"
        assert list(file_reader.df.columns) == list(file_reader_csv.df.columns), "Column names differ"
        assert all(file_reader.df.dtypes == file_reader_csv.df.dtypes), "Column types differ"

        # evaluate if units row read by csv and txt output are the same
        assert file_reader.units_row.equals(file_reader_csv.units_row)


def test_github():

    # regular GitHub trigger test function when no code is changed
    assert str(2) == '2'
