import os
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


def test_enable_disable_csv_print(
    txtinout_reader
):

    # pass test for enable CSV print
    txtinout_reader.enable_csv_print()
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[6]
    assert target_line[0] == 'y'

    # pass test for disable CSV print
    txtinout_reader.disable_csv_print()
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[6]
    assert target_line[0] == 'n'


def test_enable_object_in_print_prt(
    txtinout_reader
):

    # pass test for enable object for printing
    txtinout_reader.enable_object_in_print_prt(
        obj='basin_wb',
        daily=False,
        monthly=True,
        yearly=True,
        avann=False
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[10]
    assert ' y' in target_line
    assert target_line.count(' y') == 2
    assert ' n' in target_line
    assert target_line.count(' n') == 2

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


def test_set_begin_and_end_year(
    txtinout_reader
):

    # pass test for begining and end year
    txtinout_reader.set_begin_and_end_year(
        begin=2012,
        end=2016
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'time.sim')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[-1]
    assert '2012' in target_line
    assert '2016' in target_line
    assert '2025' not in target_line

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


def test_set_warmup_year(
    txtinout_reader
):

    # pass test for warmup year
    txtinout_reader.set_warmup_year(
        warmup=1
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[2]
    assert target_line[0] == str(1)
    assert target_line[0] != '5'

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


def test_run_swat_in_other_dir(
    txtinout_reader
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        output = txtinout_reader.run_swat_in_other_dir(
            target_dir=tmp_dir,
            begin_and_end_year=(2010, 2012),
            warmup=1,
            print_prt_control={'channel_sd': {'daily': False}}
        )
        assert os.path.samefile(output, tmp_dir)


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
