import os
import pySWATPlus
import pytest
import tempfile


@pytest.fixture(scope='class')
def data_manager():

    # initialize DataManager class
    data_manager = pySWATPlus.DataManager()

    yield data_manager


def test_simulated_timeseries_df(
    data_manager
):

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # Read DataFrame
    with tempfile.TemporaryDirectory() as tmp_dir:
        df = data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            save_df=True,
            json_file=os.path.join(tmp_dir, 'zrecall_yr.json')
        )
        assert df.shape == (1, 66)

    # error test for missing JSON file
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            save_df=True
        )
    assert exc_info.value.args[0] == 'json_file must be a valid JSON file string path when save_df=True'

    # error test for missing time series columns
    missing_cols = ['mon', 'day']
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'basin_carbon_all.txt'),
            has_units=True
        )
    assert exc_info.value.args[0] == f'Missing required time series columns "{missing_cols}" in file "basin_carbon_all.txt"'

    # error test for invalid column name to filter rows
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            apply_filter={'unavailable': 1}
        )
    assert exc_info.value.args[0] == 'Column "unavailable" in apply_filter is not present in file "zrecall_yr.txt"'

    # error test for invalid column value type
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            apply_filter={'name': 1}
        )
    assert exc_info.value.args[0] == 'Filter values for column "name" must be a list in file "zrecall_yr.txt"'

    # error test for a apply_filter that no data can be extracted
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            apply_filter={'name': ['hru007']}
        )
    # val = ['hru007']
    assert exc_info.value.args[0] == f'Filtering by column "name" with values "{['hru007']}" removed all rows from file "zrecall_yr.txt"'

    # error test for invalid start_date format
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            start_date='2025/01/01'
        )
    assert exc_info.value.args[0] == 'Invalid date format: "2025/01/01". Expected YYYY-MM-DD.'

    # error test for invalid end_date format
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            end_date='2025/01/01'
        )
    assert exc_info.value.args[0] == 'Invalid date format: "2025/01/01". Expected YYYY-MM-DD.'

    # error test for a date range that no data can be extracted
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            start_date='1900-01-01',
            end_date='1900-12-31'
        )
    assert exc_info.value.args[0] == 'No data available between "1900-01-01" and "1900-12-31" in file "zrecall_yr.txt"'

    # error test for invalid column name in usecols
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            has_units=True,
            usecols=['unavailable_column']
        )
    assert exc_info.value.args[0] == 'Column "unavailable_column" in usecols list is not present in file "zrecall_yr.txt"'
