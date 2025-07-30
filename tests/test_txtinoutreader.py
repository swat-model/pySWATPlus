import os
import pySWATPlus
import pytest
import typing
import tempfile


@pytest.fixture(scope='class')
def txtinout_reader() -> typing.Generator[pySWATPlus.TxtinoutReader, None, None]:

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data', 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=data_folder
    )

    yield txtinout_reader


def test_enable_object_in_print_prt(
    txtinout_reader: pySWATPlus.TxtinoutReader
) -> None:

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


def test_set_begin_and_end_year(
    txtinout_reader: pySWATPlus.TxtinoutReader
) -> None:

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


def test_set_warmup_year(
    txtinout_reader: pySWATPlus.TxtinoutReader
) -> None:

    # pass test for warmup year
    txtinout_reader.set_warmup_year(
        warmup=1
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[2]
    assert target_line[0] == str(1)
    assert target_line[0] != '5'


def test_run_swat_in_other_dir(
    txtinout_reader: pySWATPlus.TxtinoutReader
) -> None:

    # pass test for run SWAT+ model in other direcotry
    with tempfile.TemporaryDirectory() as tmp_dir:
        str_dir = str(tmp_dir)
        output = txtinout_reader.run_swat_in_other_dir(
            target_dir=tmp_dir,
            params={
                'hydrology.hyd': {
                    'epco': {'value': 0.75}
                }
            }
        )
        assert str(output) == str_dir

    # error test for invalid input
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat_in_other_dir(
            target_dir=1
        )
    assert exc_info.value.args[0] == "target_dir must be a string or Path object"


def test_error_txtinoutreader_class():

    # set up file path
    test_folder = os.path.dirname(__file__)

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path=1
        )
    assert exc_info.value.args[0] == "path must be a string or Path object"

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path=os.path.join(test_folder, 'sample_data', 'nonexist_folder')
        )
    assert exc_info.value.args[0] == "Folder does not exist"

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path=os.path.join(test_folder, 'sample_data', 'no_exe')
        )
    assert exc_info.value.args[0] == "Expected exactly one .exe file in the parent folder, but found none or multiple."
