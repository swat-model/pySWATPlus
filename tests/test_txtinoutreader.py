import os
import pySWATPlus
import pytest
import typing


@pytest.fixture(scope='class')
def txtinout_reader() -> typing.Generator[pySWATPlus.TxtinoutReader, None, None]:

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data')

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
        begin=2015,
        end=2020
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'time.sim')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[-1]
    assert '2015' in target_line
    assert '2020' in target_line
    assert '2025' not in target_line

    # pass test for warmup year
    txtinout_reader.set_begin_and_end_year(
        begin=2015,
        end=2025
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'time.sim')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[-1]
    assert '2015' in target_line
    assert '2020' not in target_line
    assert '2025' in target_line


def test_set_warmup_year(
    txtinout_reader: pySWATPlus.TxtinoutReader
) -> None:

    # pass test for warmup year
    txtinout_reader.set_warmup_year(
        warmup=3
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[2]
    assert target_line[0] == str(3)
    assert target_line[0] != '5'
