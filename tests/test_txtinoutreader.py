import os
import pySWATPlus
import pytest


@pytest.fixture(scope='class')
def txtinout_reader():

    # set up file path
    test_folder = os.path.dirname(__file__)
    data_folder = os.path.join(test_folder, 'sample_data')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=data_folder
    )

    yield txtinout_reader


def test_set_begin_and_end_year(
    txtinout_reader
):

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
    txtinout_reader
):

    # pass test for warmup year
    txtinout_reader.set_warmup_year(
        warmup=3
    )
    output_file = os.path.join(str(txtinout_reader.root_folder), 'print.prt')
    with open(output_file, 'r') as read_output:
        target_line = read_output.readlines()[2]
    assert target_line[0] == str(3)
    assert target_line[0] != 5
