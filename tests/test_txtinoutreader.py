import os
import pandas
import pySWATPlus
import pytest
import tempfile


@pytest.fixture(scope='class')
def txtinout_reader():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    yield txtinout_reader


def test_reader_error(
    txtinout_reader
):

    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Intialize TxtinOutReader class by target direcotry
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )
        # pass test for enable CSV print
        target_reader.enable_csv_print()
        printprt_file = os.path.join(str(target_reader.root_folder), 'print.prt')
        with open(printprt_file, 'r') as read_output:
            target_line = read_output.readlines()[6]
        assert target_line[0] == 'y'
        # pass test to update all objects in print.prt
        target_reader.enable_object_in_print_prt(
            obj=None,
            daily=False,
            monthly=False,
            yearly=True,
            avann=True
        )
        with open(printprt_file, 'r') as f:
            lines = f.readlines()[10:]  # skip first 10 unchanged lines
        for line in lines:
            if line.strip():
                assert line.split()[1] == 'n'
                assert line.split()[2] == 'n'
                assert line.split()[3] == 'y'
                assert line.split()[4] == 'y'
        with tempfile.TemporaryDirectory() as tmp2_dir:
            # pass test for run SWAT+ in other directory
            target_dir = target_reader.run_swat_in_other_dir(
                target_dir=tmp2_dir,
                begin_and_end_year=(2010, 2012),
                warmup=1,
                print_prt_control={'channel_sd': {'daily': False}}
            )
            assert os.path.samefile(target_dir, tmp2_dir)
            # pass test to ensure data types are parsed correctly (for example jday must be int)
            file_reader = pySWATPlus.FileReader(
                path=os.path.join(str(target_dir), 'channel_sd_yr.txt'),
                has_units=True
            )
            df = file_reader.df
            assert pandas.api.types.is_integer_dtype(df['jday'])
            # pass test to read CSV file
            csv_file_reader = pySWATPlus.FileReader(
                path=os.path.join(str(target_dir), 'channel_sd_yr.csv'),
                has_units=True
            )
            csv_df = csv_file_reader.df
            # pass test TXT and CSV file DataFrames
            assert df.shape == csv_df.shape
            assert list(df.columns) == list(csv_df.columns)
            assert all(df.dtypes == csv_df.dtypes)
            assert file_reader.units_row.equals(csv_file_reader.units_row)
            # error for overwriting output file
            with pytest.raises(Exception) as exc_info:
                file_reader = pySWATPlus.FileReader(
                    path=os.path.join(str(target_dir), 'channel_sd_yr.txt'),
                    has_units=True
                )
                file_reader.overwrite_file()
            assert exc_info.value.args[0] == 'Overwriting SWAT+ Output Files is not allowed'
            # Initialize TxtInoutReader class
            target_reader = pySWATPlus.TxtinoutReader(
                path=target_dir
            )
            # pass test for adding invalid object with flag
            target_reader.enable_object_in_print_prt(
                obj='my_custom_obj',
                daily=True,
                monthly=False,
                yearly=False,
                avann=True,
                allow_unavailable_object=True
            )
            printprt_file = os.path.join(str(target_reader.root_folder), 'print.prt')
            with open(printprt_file, 'r') as f:
                lines = f.readlines()
            assert any(line.startswith('my_custom_obj') for line in lines)
            assert ' y' in lines[-1]
            # pass test for disable CSV print
            target_reader.disable_csv_print()
            with open(printprt_file, 'r') as read_output:
                target_line = read_output.readlines()[6]
            assert target_line[0] == 'n'


def test_error_enable_object_in_print_prt(
    txtinout_reader
):

    # error test for 'obj' type
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj=1,
            daily=True,
            monthly=True,
            yearly=True,
            avann=False
        )
    assert exc_info.value.args[0] == 'Input "obj" to be string type or None, got int'

    # error test for invalid bool value
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj='basin_wb',
            daily=5,
            monthly=True,
            yearly=True,
            avann=False
        )
    assert exc_info.value.args[0] == 'Variable "daily" for "basin_wb" must be a bool value'

    # error test for adding invalid object without flag
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj='invalid_obj',
            daily=True,
            monthly=True,
            yearly=True,
            avann=False,
            allow_unavailable_object=False
        )
    assert exc_info.value.args[0] == 'Object "invalid_obj" not found in print.prt file. Use allow_unavailable_object=True to proceed.'


def test_error_txtinoutreader_class():

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path=1
        )
    assert exc_info.value.args[0] == 'path must be a string or Path object'

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path='nonexist_folder'
        )
    assert exc_info.value.args[0] == 'Folder does not exist'

    # error test for .exe file
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.TxtinoutReader(
                path=tmp_dir
            )
        assert exc_info.value.args[0] == 'Expected exactly one .exe file in the parent folder, but found none or multiple.'


def test_error_set_begin_and_end_year(
    txtinout_reader
):

    # error test for float value in begin and end years
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.set_begin_and_end_year(
            begin=2012.0,
            end=2016
        )
    assert exc_info.value.args[0] == '"begin" year must be an integer value'
    # error test for begin year is greater than end year
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.set_begin_and_end_year(
            begin=2016,
            end=2012
        )
    assert exc_info.value.args[0] == 'begin year must be less than end year'


def test_error_set_warmup_year(
    txtinout_reader
):

    # error test for float value in warmup years
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.set_warmup_year(
            warmup=1.0
        )
    assert exc_info.value.args[0] == 'warmup must be an integer value'
    # error test for warm-up year is equal to 0
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.set_warmup_year(
            warmup=0
        )
    assert exc_info.value.args[0] == 'warmup must be a positive integer'


def test_error_run_swat_in_other_dir(
    txtinout_reader
):

    # error test for invalid folder path
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat_in_other_dir(
            target_dir=1
        )
    assert exc_info.value.args[0] == 'target_dir must be a string or Path object'

    with tempfile.TemporaryDirectory() as tmp_dir:
        # error test for invalid begin and end year values type
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                begin_and_end_year=[]
            )
        assert exc_info.value.args[0] == 'begin_and_end_year must be a tuple'
        # error test for invalid begin and end years tuple length
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                begin_and_end_year=(1, 2, 3)
            )
        assert exc_info.value.args[0] == 'begin_and_end_year must contain exactly two elements'
        # error test for invalid print_prt_control type
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                print_prt_control=[]
            )
        assert exc_info.value.args[0] == 'print_prt_control must be a dictionary'
        # error test for empty print_prt_control dictionary
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                print_prt_control={}
            )
        assert exc_info.value.args[0] == 'print_prt_control cannot be an empty dictionary'
        # error test for invalid sub key value type of print_prt_control
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                print_prt_control={'basin_wb': []}
            )
        assert exc_info.value.args[0] == 'Value of key "basin_wb" must be a dictionary'
        # error test for empty dictionary of sub key of print_prt_control
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                print_prt_control={'basin_wb': {}}
            )
        assert exc_info.value.args[0] == 'Value of key "basin_wb" cannot be an empty dictionary'
        # error test for invalid time fequency
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                print_prt_control={'basin_wb': {'dailyy': False}}
            )
        assert exc_info.value.args[0] == 'Sub-key "dailyy" for key "basin_wb" is not valid'
        # error test for subprocess.CalledProcessError
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat_in_other_dir(
                target_dir=tmp_dir,
                params={
                    'plants.plt': {
                        'has_units': False,
                        'bm_e': {'value': 200, 'filter_by': 'name == "agrl"'}
                    },
                }
            )
        assert exc_info.value.args[0] == 65


def test_error_print_prt_does_not_exist(
    txtinout_reader
):
    # check that exception is raised if print.prt file does not exist
    with tempfile.TemporaryDirectory() as tmp1_dir:
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # delete print.prt file in tmp1_dir
        print_prt_path = target_dir / 'print.prt'
        if print_prt_path.exists():
            print_prt_path.unlink()

        with pytest.raises(Exception) as exc_info:
            target_reader.enable_object_in_print_prt(
                obj='basin_wb',
                daily=False,
                monthly=True,
                yearly=True,
                avann=False
            )
        assert exc_info.value.args[0] == 'print.prt file does not exist'

        with pytest.raises(Exception) as exc_info:
            target_reader.set_warmup_year(3)
        assert exc_info.value.args[0] == 'print.prt file does not exist'

        with pytest.raises(Exception) as exc_info:
            target_reader.enable_csv_print()
        assert exc_info.value.args[0] == 'print.prt file does not exist'

        with pytest.raises(Exception) as exc_info:
            target_reader.disable_csv_print()
        assert exc_info.value.args[0] == 'print.prt file does not exist'


def test_error_time_sim_does_not_exist(
    txtinout_reader
):
    # check that exception is raised if time.sim file does not exist
    with tempfile.TemporaryDirectory() as tmp1_dir:
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # delete time.sim file in tmp1_dir
        time_sim_path = target_dir / 'time.sim'
        if time_sim_path.exists():
            time_sim_path.unlink()

        with pytest.raises(Exception) as exc_info:
            target_reader.set_begin_and_end_year(
                begin=2000,
                end=2020
            )
        assert exc_info.value.args[0] == 'time.sim file does not exist'
